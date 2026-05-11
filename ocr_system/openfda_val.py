"""
validate_inn_openfda.py
=======================
Validates every cleaned INN in cleaned_inn_unique.json against the
OpenFDA API and writes a full report.

Usage
-----
    python validate_inn_openfda.py
    python validate_inn_openfda.py --input cleaned_inn_unique.json
    python validate_inn_openfda.py --workers 8      # parallel requests (faster)
    python validate_inn_openfda.py --limit 100      # validate first N INNs only

Outputs
-------
    openfda_validation_report.json   full machine-readable report
    openfda_validation_report.csv    spreadsheet-friendly summary
    openfda_misses.json              only the misses (easy to review)

OpenFDA API used
----------------
    https://api.fda.gov/drug/label.json
    https://api.fda.gov/drug/drugsfda.json
    Rate limit: 240 requests/minute with API key, 40/minute without.
    Get a free key at https://open.fda.gov/apis/authentication/
    Set it via:  export OPENFDA_API_KEY="your_key_here"
"""

import json, re, time, os, csv, sys, argparse
import urllib.request, urllib.parse, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ── OpenFDA endpoints ─────────────────────────────────────────────────────────
LABEL_URL     = "https://api.fda.gov/drug/label.json"
DRUGSFDA_URL  = "https://api.fda.gov/drug/drugsfda.json"

API_KEY = "bCJ7ykUPozw7jlixyA8i0MyKPuxszvg6sskKjol9"

# ── Salt suffixes to strip when trying a base-INN fallback ───────────────────
_SALT_SFXS = [
    " hydrochloride", " dihydrochloride", " sulfate", " besylate", " mesylate",
    " maleate", " fumarate", " tartrate", " bitartrate", " phosphate", " acetate",
    " benzoate", " valerate", " decanoate", " propionate", " dipropionate",
    " nitrate", " bromide", " iodide", " chloride", " lactate", " citrate",
    " oxalate", " gluconate", " digluconate", " sodium", " potassium", " calcium",
    " magnesium", " medoxomil", " pivoxil", " proxetil", " axetil", " cilexetil",
    " etexilate", " meglumine", " dimaleate", " succinate", " folinate",
    " disodium phosphate", " monosodium phosphate", " subcitrate",
]

def _strip_salt(inn: str) -> str:
    """Return base INN with the first matching salt suffix removed."""
    low = inn.lower()
    for sfx in _SALT_SFXS:
        if low.endswith(sfx):
            return inn[: -len(sfx)].strip()
    return inn


def _build_url(base: str, field: str, value: str, limit: int = 1) -> str:
    """Build a properly-encoded OpenFDA query URL."""
    key_param = f"&api_key={API_KEY}" if API_KEY else ""
    encoded   = urllib.parse.quote(f'"{value}"')
    return f"{base}?search={field}:{encoded}&limit={limit}{key_param}"


def _fetch(url: str, timeout: int = 10) -> dict | None:
    """GET url, return parsed JSON or None on any error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "inn-validator/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:        # no results — expected miss
            return {"results": []}
        if e.code == 429:        # rate-limited
            time.sleep(2)
            return None
        return None
    except Exception:
        return None


def _hit_from_body(body: dict | None) -> str | None:
    """
    Return the matched generic_name string if body contains results,
    else None.
    """
    if not body or not body.get("results"):
        return None
    r = body["results"][0]
    gn = r.get("openfda", {}).get("generic_name")
    if gn:
        return gn[0]
    # drugsfda endpoint: active_ingredients list
    ai = r.get("active_ingredients") or r.get("products", [{}])[0].get("active_ingredients", [])
    if ai and isinstance(ai, list) and ai[0].get("name"):
        return ai[0]["name"]
    return "FOUND (no generic_name field)"


# ── Core validation logic for a single INN ───────────────────────────────────

def validate_inn(inn: str, timeout: int = 10) -> dict:
    """
    Try to find `inn` in OpenFDA using a waterfall of strategies.
    Returns a dict with keys:
        inn          – the input INN
        hit          – True / False
        matched_name – what OpenFDA returned (or None)
        strategy     – which strategy succeeded (or 'miss')
        candidates   – list of strings attempted
    """
    result = {
        "inn": inn,
        "hit": False,
        "matched_name": None,
        "strategy": "miss",
        "candidates": [],
    }

    # Build candidate list (ordered: most-specific → most-lenient)
    candidates: list[tuple[str, str, str]] = []   # (description, endpoint, field)

    # ── Strategy 1: openfda.generic_name on label endpoint ───────────────────
    candidates.append(("label/generic_name", inn, "label/openfda.generic_name"))

    # ── Strategy 2: same field on drugsfda endpoint ───────────────────────────
    candidates.append(("drugsfda/generic_name", inn, "drugsfda/openfda.generic_name"))

    # ── Strategy 3: first component (for combos) ─────────────────────────────
    first = inn.split("/")[0].strip() if "/" in inn else None
    if first and first != inn:
        candidates.append(("label/generic_name[first]", first, "label/openfda.generic_name"))

    # ── Strategy 4: base INN (salt stripped) ─────────────────────────────────
    base = _strip_salt(inn)
    if base != inn:
        candidates.append(("label/generic_name[base]", base, "label/openfda.generic_name"))
        candidates.append(("drugsfda/generic_name[base]", base, "drugsfda/openfda.generic_name"))

    # ── Strategy 5: first component base INN ─────────────────────────────────
    if first:
        first_base = _strip_salt(first)
        if first_base != first:
            candidates.append(("label/generic_name[first_base]", first_base, "label/openfda.generic_name"))

    # ── Strategy 6: broad generic_name text field ─────────────────────────────
    candidates.append(("label/generic_name_text", inn, "label/generic_name"))
    if base != inn:
        candidates.append(("label/generic_name_text[base]", base, "label/generic_name"))

    already: set[str] = set()

    for strategy_label, query_value, endpoint_field in candidates:
        if query_value in already or not query_value.strip():
            continue
        already.add(query_value)
        result["candidates"].append(query_value)

        endpoint, field = endpoint_field.split("/", 1)
        base_url = LABEL_URL if endpoint == "label" else DRUGSFDA_URL
        url = _build_url(base_url, field, query_value)

        body = _fetch(url, timeout=timeout)
        if body is None:
            # Transient error — wait and retry once
            time.sleep(1.5)
            body = _fetch(url, timeout=timeout)

        matched = _hit_from_body(body)
        if matched:
            result["hit"]          = True
            result["matched_name"] = matched
            result["strategy"]     = strategy_label
            return result

        # Respect rate limit: ~40 req/min without key, ~240 with key
        time.sleep(0.05 if API_KEY else 0.25)

    return result


# ── Batch runner ──────────────────────────────────────────────────────────────

def run_validation(
    inn_list: list[str],
    workers: int = 4,
    timeout: int = 10,
    progress: bool = True,
) -> list[dict]:
    """Validate a list of INNs, optionally in parallel."""
    results = []
    total   = len(inn_list)
    done    = 0

    if workers <= 1:
        for inn in inn_list:
            r = validate_inn(inn, timeout=timeout)
            results.append(r)
            done += 1
            if progress:
                sym = "✓" if r["hit"] else "✗"
                note = f"  [{r['strategy']}]" if r["hit"] else ""
                print(f"  [{done:4}/{total}] {sym}  {inn}{note}")
    else:
        futures_map = {}
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for inn in inn_list:
                f = ex.submit(validate_inn, inn, timeout)
                futures_map[f] = inn
            for f in as_completed(futures_map):
                r = f.result()
                results.append(r)
                done += 1
                if progress:
                    sym  = "✓" if r["hit"] else "✗"
                    note = f"  [{r['strategy']}]" if r["hit"] else ""
                    print(f"  [{done:4}/{total}] {sym}  {r['inn']}{note}")

    # Re-sort to match original order
    order = {inn: i for i, inn in enumerate(inn_list)}
    results.sort(key=lambda r: order.get(r["inn"], 9999))
    return results


# ── Report writers ────────────────────────────────────────────────────────────

def write_json_report(results: list[dict], path: Path) -> None:
    hits   = [r for r in results if r["hit"]]
    misses = [r for r in results if not r["hit"]]
    total  = len(results)
    report = {
        "summary": {
            "total": total,
            "hits": len(hits),
            "misses": len(misses),
            "hit_rate_pct": round(len(hits) / total * 100, 1) if total else 0,
        },
        "hits":   hits,
        "misses": misses,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def write_csv_report(results: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["inn", "hit", "matched_name", "strategy", "candidates_tried"])
        for r in results:
            w.writerow([
                r["inn"],
                "yes" if r["hit"] else "no",
                r.get("matched_name") or "",
                r.get("strategy") or "",
                " | ".join(r.get("candidates", [])),
            ])


def write_misses_json(results: list[dict], path: Path) -> None:
    misses = [r for r in results if not r["hit"]]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(misses, f, ensure_ascii=False, indent=2)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Validate cleaned INNs against OpenFDA")
    ap.add_argument("--input",   default="C:\\Users\\LENOVO\\Code\\PFE\\ocr_system\\data\\cleaned_inn_unique.json",
                    help="Path to cleaned_inn_unique.json")
    ap.add_argument("--output-dir", default="C:\\Users\\LENOVO\\Code\\PFE\\ocr_system\\Results",
                    help="Directory for output files")
    ap.add_argument("--workers", type=int, default=1,
                    help="Parallel workers (default 1; use 4–8 with an API key)")
    ap.add_argument("--limit",   type=int, default=0,
                    help="Only validate first N INNs (0 = all)")
    ap.add_argument("--timeout", type=int, default=10,
                    help="Per-request timeout in seconds")
    args = ap.parse_args()

    # Load
    p = Path(args.input)
    if not p.exists():
        p = Path("cleaned_inn_unique.json")
    with open(p, encoding="utf-8") as f:
        raw: dict = json.load(f)

    # De-duplicate the cleaned INN values (we validate INNs, not raw DCIs)
    inn_list = list(dict.fromkeys(raw.values()))   # preserves order, removes dupes
    if args.limit:
        inn_list = inn_list[: args.limit]

    total = len(inn_list)
    combos  = sum(1 for inn in inn_list if "/" in inn)
    singles = total - combos
    print(f"\nLoaded {total} unique INNs  ({singles} single, {combos} combinations)")
    if API_KEY:
        print(f"API key detected — higher rate limit enabled (workers={args.workers})")
    else:
        print("No API key — rate-limited to ~40 req/min (set OPENFDA_API_KEY to go faster)")
    eta_min = total * (0.3 if API_KEY else 1.6) / 60 / max(1, args.workers)
    print(f"Estimated time: ~{eta_min:.1f} min\n")

    # Run
    results = run_validation(inn_list, workers=args.workers, timeout=args.timeout)

    # Summarise
    hits    = sum(1 for r in results if r["hit"])
    misses  = total - hits
    rate    = hits / total * 100 if total else 0
    print(f"\n{'─'*60}")
    print(f"  Hit rate : {hits}/{total}  ({rate:.1f}%)")
    print(f"  Misses   : {misses}")

    # Strategy breakdown
    from collections import Counter
    strats = Counter(r["strategy"] for r in results)
    print("\n  Strategy breakdown:")
    for s, n in strats.most_common():
        print(f"    {s:<40} {n}")

    # Write outputs
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    report_path = out / "openfda_validation_report.json"
    csv_path    = out / "openfda_validation_report.csv"
    miss_path   = out / "openfda_misses.json"

    write_json_report(results, report_path)
    write_csv_report(results, csv_path)
    write_misses_json(results, miss_path)

    print(f"\n  Wrote {report_path}")
    print(f"  Wrote {csv_path}")
    print(f"  Wrote {miss_path}")
    print("\nDone.")


if __name__ == "__main__":
    main()