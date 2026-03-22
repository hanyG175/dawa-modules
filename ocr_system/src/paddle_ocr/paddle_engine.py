"""PaddleOCR engine - simple wrapper around PaddleOCR library."""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np

# Must be set before importing PaddleOCR
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['GLOG_minloglevel'] = '3'

try:
    from paddleocr import PaddleOCR
except ImportError:
    raise ImportError("Install PaddleOCR with: pip install paddleocr")

try:
    from paddleocr import PPStructure
except Exception:
    PPStructure = None

logger = logging.getLogger(__name__)


class PaddleEngine:
    """Simple PaddleOCR wrapper for text extraction."""
    
    def __init__(
        self,
        languages: Optional[List[str]] = None,
        use_gpu: bool = False,
        enable_layout: bool = True,
    ):
        """
        Initialize OCR engine.
        
        Args:
            languages: Language codes (default: ["en"])
            use_gpu: Use GPU acceleration (default: False)
            enable_layout: Enable PP-Structure page layout detection when available
        """
        self.languages = list(dict.fromkeys(languages or ["fr"]))
        self.use_gpu = use_gpu
        self.enable_layout = enable_layout

        # PaddleOCR supports one language model per engine instance.
        # Build one engine per requested language.
        self.ocr_engines: Dict[str, PaddleOCR] = {}
        for lang in self.languages:
            try:
                logger.info(f"Initializing PaddleOCR with language: {lang}")
                self.ocr_engines[lang] = PaddleOCR(
                    use_angle_cls=True,
                    lang=lang,
                    use_gpu=use_gpu,
                    show_log=False,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize PaddleOCR for language '{lang}': {str(e)}")

        if not self.ocr_engines:
            raise RuntimeError("No PaddleOCR language model could be initialized.")

        # Keep a default engine alias for compatibility
        self.ocr = next(iter(self.ocr_engines.values()))

        # Optional layout analysis engine (titles, tables, text regions, etc.)
        self.layout_engine = None
        if self.enable_layout and PPStructure is not None:
            try:
                self.layout_engine = PPStructure(show_log=False, use_gpu=use_gpu)
            except Exception as e:
                logger.warning(f"Failed to initialize PPStructure layout engine: {str(e)}")
    
    def extract_text(self, image_input: Any) -> Dict[str, Any]:
        """
        Extract text from image.
        
        Args:
            image_input: Image path, numpy array, or PIL image
            
        Returns:
            Dictionary with 'text', 'confidence', and 'success' keys
        """
        try:
            logger.info(f"Extracting text from: {image_input}")
            prepared_input = self._prepare_input(image_input)
            best_result = {"text": "", "confidence": 0.0, "success": False}
            best_language = None
            errors: Dict[str, str] = {}
            language_results: Dict[str, Dict[str, Any]] = {}
            merged_lines: List[str] = []
            seen_lines = set()

            for lang, ocr_engine in self.ocr_engines.items():
                try:
                    results = ocr_engine.ocr(prepared_input, cls=True)

                    if not results or not results[0]:
                        continue

                    # Extract text and confidence
                    texts = []
                    confidences = []
                    line_items = []
                    for line in results[0]:
                        if len(line) > 1 and len(line[1]) >= 2:
                            box = line[0]
                            text = line[1][0]
                            confidence = float(line[1][1])
                            if text:
                                texts.append(text)
                                confidences.append(confidence)
                                line_items.append(
                                    {
                                        "text": text,
                                        "confidence": confidence,
                                        "bbox": box,
                                    }
                                )

                    direction = "rtl" if set(self.languages) == {"ar"} else "ltr"
                    line_items = self._sort_items_by_reading_order(line_items, direction=direction)
                    texts = [item["text"] for item in line_items]

                    full_text = "\n".join(texts)
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

                    language_results[lang] = {
                        "text": full_text,
                        "confidence": avg_confidence,
                        "success": bool(full_text),
                        "lines": line_items,
                    }

                    for txt_line in texts:
                        normalized = txt_line.strip()
                        if normalized and normalized not in seen_lines:
                            seen_lines.add(normalized)
                            merged_lines.append(normalized)

                    if full_text and avg_confidence >= best_result["confidence"]:
                        best_result = {
                            "text": full_text,
                            "confidence": avg_confidence,
                            "success": True,
                        }
                        best_language = lang
                except Exception as e:
                    errors[lang] = str(e)
                    continue

            merged_text = "\n".join(merged_lines)
            successful_languages = [
                lang for lang, lang_result in language_results.items() if lang_result.get("success")
            ]
            merged_confidence = (
                sum(language_results[lang]["confidence"] for lang in successful_languages) / len(successful_languages)
                if successful_languages
                else 0.0
            )

            if merged_text:
                logger.info(
                    f"Extracted multilingual text from {len(successful_languages)} language(s); "
                    f"best='{best_language}', merged_confidence={merged_confidence:.2%}"
                )
                result = {
                    "text": merged_text,
                    "confidence": merged_confidence,
                    "success": True,
                    "language": best_language,
                    "detected_languages": successful_languages,
                    "language_results": language_results,
                }
                if errors:
                    result["language_errors"] = errors
                return result

            result = {"text": "", "confidence": 0.0, "success": False}
            if language_results:
                result["language_results"] = language_results
            if errors:
                result["language_errors"] = errors
            return result
        except Exception as e:
            logger.error(f"OCR extraction error: {str(e)}")
            return {"text": "", "confidence": 0.0, "success": False, "error": str(e)}

    def extract_layout(self, image_input: Any) -> Dict[str, Any]:
        """Extract document layout blocks (title/table/text/figure) with PPStructure."""
        if self.layout_engine is None:
            return {
                "success": False,
                "error": "Layout engine not available. Install PaddleOCR with PPStructure support and enable_layout=True.",
            }

        try:
            prepared_input = self._prepare_input(image_input)
            results = self.layout_engine(prepared_input)

            blocks = []
            for block in results or []:
                block_type = block.get("type")
                bbox = block.get("bbox")
                text = ""

                block_res = block.get("res")
                if isinstance(block_res, list):
                    texts = [item.get("text", "") for item in block_res if isinstance(item, dict)]
                    text = "\n".join([t for t in texts if t])

                blocks.append({
                    "type": block_type,
                    "bbox": bbox,
                    "text": text,
                })

            direction = "rtl" if set(self.languages) == {"ar"} else "ltr"
            blocks = self._sort_items_by_reading_order(blocks, direction=direction)

            return {
                "success": True,
                "blocks": blocks,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _prepare_input(self, image_input: Any) -> Any:
        """Prepare input for PaddleOCR v2 `ocr()` API."""
        if isinstance(image_input, (str, Path)):
            return str(image_input)

        if isinstance(image_input, np.ndarray):
            return image_input

        # Handle PIL images without forcing PIL import dependency at module load
        if hasattr(image_input, "mode") and hasattr(image_input, "size"):
            try:
                return np.array(image_input)
            except Exception:
                pass

        raise TypeError("Unsupported image input type. Use file path, numpy.ndarray, or PIL image.")

    def _sort_items_by_reading_order(self, items: List[Dict[str, Any]], direction: str = "ltr") -> List[Dict[str, Any]]:
        """Sort OCR/layout items with two-column aware reading order."""
        if not items:
            return items

        stats = [self._bbox_stats(item.get("bbox")) for item in items]
        valid_stats = [s for s in stats if s is not None]
        if not valid_stats:
            return items

        # Estimate whether page looks like two columns using horizontal centers.
        centers = sorted([s["x_center"] for s in valid_stats])
        if len(centers) < 6:
            return self._sort_single_column(items, direction)

        mid = len(centers) // 2
        left_center = float(np.median(centers[:mid]))
        right_center = float(np.median(centers[mid:]))
        page_width = max(s["x_max"] for s in valid_stats) - min(s["x_min"] for s in valid_stats)
        center_gap = right_center - left_center

        # If there is no strong separation, keep standard order.
        if page_width <= 0 or center_gap < page_width * 0.2:
            return self._sort_single_column(items, direction)

        threshold = (left_center + right_center) / 2.0
        left_items, right_items = [], []

        for item in items:
            s = self._bbox_stats(item.get("bbox"))
            if s is None:
                continue
            if s["x_center"] <= threshold:
                left_items.append(item)
            else:
                right_items.append(item)

        left_items = self._sort_single_column(left_items, direction="ltr")
        right_items = self._sort_single_column(right_items, direction="ltr")

        if direction == "rtl":
            return right_items + left_items
        return left_items + right_items

    def _sort_single_column(self, items: List[Dict[str, Any]], direction: str = "ltr") -> List[Dict[str, Any]]:
        """Sort one text column top-to-bottom then horizontal direction."""
        def _key(item: Dict[str, Any]):
            s = self._bbox_stats(item.get("bbox"))
            if s is None:
                return (0.0, 0.0)
            x_key = -s["x_min"] if direction == "rtl" else s["x_min"]
            return (s["y_min"], x_key)

        return sorted(items, key=_key)

    def _bbox_stats(self, bbox: Any) -> Optional[Dict[str, float]]:
        """Get bbox min/max/center stats for both polygon and rectangle formats."""
        if not bbox:
            return None

        # Polygon format: [[x,y], [x,y], [x,y], [x,y]]
        if isinstance(bbox, list) and len(bbox) >= 4 and isinstance(bbox[0], (list, tuple)):
            x_vals = [float(p[0]) for p in bbox if isinstance(p, (list, tuple)) and len(p) >= 2]
            y_vals = [float(p[1]) for p in bbox if isinstance(p, (list, tuple)) and len(p) >= 2]
            if not x_vals or not y_vals:
                return None
            x_min, x_max = min(x_vals), max(x_vals)
            y_min, y_max = min(y_vals), max(y_vals)
        # Rectangle format: [x1, y1, x2, y2]
        elif isinstance(bbox, list) and len(bbox) == 4 and all(isinstance(v, (int, float)) for v in bbox):
            x1, y1, x2, y2 = [float(v) for v in bbox]
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)
        else:
            return None

        return {
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max,
            "x_center": (x_min + x_max) / 2.0,
            "y_center": (y_min + y_max) / 2.0,
        }
