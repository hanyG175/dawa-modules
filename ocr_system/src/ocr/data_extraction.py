"""Data extraction and formatting for OCR results."""

import csv
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict

from .interfaces import OCRResult, ExtractedData

logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Extracts and formats structured data from OCR results.
    Tuned for French pharmaceutical notices (e.g., ANSM formats).
    """

    def __init__(self):
        """Initialize data extractor."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.section_heading_pattern = re.compile(r'^\s*(\d+\.\s+[^\n]+)$', re.MULTILINE)
        self.bullet_markers = ('·', '•', '\u2022')

        self.prescription_keywords = {
            "rx", "prescription", "prescrit", "dosage", "dose", "mg", "ml",
            "comprimés", "tablets", "capsules", "injection", "inhalation",
            "posologie", "posology", "administration", "usage", "application",
            "voie d'administration", "fréquence", "durée"
        }

        self.medicine_keywords = {
            "medicine", "drug", "medicament", "médicament", "active substance",
            "substance active", "brand name", "nom commercial", "product",
            "dénomination", "substance active"
        }

        self.french_section_keywords = {
            "dénomination du médicament", "substance active", "indications thérapeutiques",
            "contre-indications", "contraindications", "effets indésirables",
            "posologie", "mode et voie d'administration", "comment conserver",
            "conditions de conservation", "titulaire", "fabricant", "exploitant",
            "liste des excipients"
        }

    def extract_from_ocr_result(
        self,
        ocr_result: OCRResult,
        source_file: Optional[str] = None
    ) -> ExtractedData:
        """
        Extract structured data from OCR result.
        Supports both English and French pharmaceutical documents.

        Args:
            ocr_result: OCRResult object from OCR engine
            source_file: Optional source file path

        Returns:
            ExtractedData object with structured information
        """
        original_text = ocr_result.raw_text or ""
        cleaned_text = self._preprocess_text(original_text)
        sections = self._extract_sections(cleaned_text)

        medicine_names = self._extract_medicine_names(cleaned_text, sections)
        prescription_info = self._extract_prescription_info(cleaned_text, sections)

        extracted_fields = self._extract_fields(cleaned_text, sections)
        manufacturer_info = self._extract_manufacturer_info(cleaned_text, sections)
        extracted_fields.update(manufacturer_info)

        regulatory_info = self._extract_regulatory_info(cleaned_text)
        extracted_fields.update(regulatory_info)

        metadata = {
            "source_type": ocr_result.source_type,
            "ocr_confidence": ocr_result.confidence,
            "source_file": source_file,
            "extraction_method": "regex_pattern_matching_multilingual"
        }
        metadata.update(ocr_result.metadata)

        return ExtractedData(
            medicine_names=medicine_names,
            prescription_info=prescription_info,
            raw_text=original_text,
            extracted_fields=extracted_fields,
            metadata=metadata
        )

    def _preprocess_text(self, text: str) -> str:
        """Normalize bullets and whitespace to simplify downstream parsing."""
        if not text:
            return ""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        for marker in self.bullet_markers:
            normalized = normalized.replace(marker, "\n- ")
        normalized = re.sub(r'\n{3,}', '\n\n', normalized)
        return normalized

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Split the notice by numbered ANSM headings (1., 2., etc.)."""
        sections: Dict[str, str] = {}
        matches = list(self.section_heading_pattern.finditer(text))
        if not matches:
            return sections

        for idx, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            normalized_title = self._normalize_heading(title)
            sections[normalized_title] = text[start:end].strip()

        return sections

    def _normalize_heading(self, heading: str) -> str:
        heading = re.sub(r'^\d+\.\s*', '', heading.strip())
        heading = heading.replace("’", "'")
        heading = self._strip_accents(heading.lower())
        heading = re.sub(r'\s+', ' ', heading)
        return heading

    def _strip_accents(self, text: str) -> str:
        return ''.join(
            char for char in unicodedata.normalize('NFD', text)
            if not unicodedata.combining(char)
        )

    def _find_section(self, sections: Dict[str, str], keywords: List[str]) -> str:
        if not sections:
            return ""
        normalized_keywords = [self._strip_accents(keyword.lower()) for keyword in keywords]
        for title, block in sections.items():
            normalized_title = self._strip_accents(title.lower())
            if any(keyword in normalized_title for keyword in normalized_keywords):
                return block
        return ""

    def _extract_medicine_names(
        self,
        text: str,
        sections: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Extract potential medicine names from text.
        Filters out section headers and question text.
        """
        names: List[str] = []

        # Extract from "Dénomination du médicament" header
        denom_pattern = re.compile(
            r'D[ée]nomination\s+du\s+m[ée]dicament\s*(?:[:\-–])?\s*([^\n]+)',
            re.IGNORECASE
        )
        for match in denom_pattern.findall(text):
            name = match.strip()
            # Filter out section header fragments
            if name and not re.search(r'^(QUE|UTILISER|COMMENT|QUELLES?|QUELS?)', name, re.IGNORECASE):
                names.append(name)

        # Pattern for dosage format: "MEDICAMENT 2 mg, comprimé"
        dosage_name_pattern = re.compile(
            r'\b([A-Z][A-Z0-9\-\s]*?)\s+(?:comprimé|injectable?|solution|sirop|gélule)',
            re.IGNORECASE
        )
        
        for line in text.splitlines():
            line = line.strip()
            if not line or len(line) > 150:
                continue
            
            # Skip lines that look like section headers or questions
            if re.match(r'^\d+\.|QUE|COMMENT|QUELS?|QUELLES?|N[\'`]', line, re.IGNORECASE):
                continue
            
            # Match: NAME with DOSAGE pattern
            if "mg" in line.lower() and re.search(r'[A-Z]{3,}', line):
                match = re.search(
                    r'([A-Z][A-Za-z0-9\s\-]+?)\s+(?:comprimé|injectable?|solution|sirop|gélule|dispersible)',
                    line,
                    re.IGNORECASE
                )
                if match:
                    candidate = match.group(1).strip()
                    if len(candidate) < 100:
                        names.append(candidate)
                else:
                    # Fallback: take first part before comma
                    parts = line.split(',')
                    if parts and len(parts[0]) < 100:
                        names.append(parts[0].strip())

        # Deduplicate and filter out non-medicine strings
        seen = set()
        unique_names = []
        for name in names:
            name_normalized = name.upper().strip()
            if (name_normalized not in seen and 
                name and len(name) < 150 and 
                "notice" not in name.lower() and
                not re.match(r'^(ET|DANS|CAS|EST|QUELS?|QUELLES?)', name_normalized, re.IGNORECASE)):
                seen.add(name_normalized)
                unique_names.append(name)

        self.logger.debug("Extracted %d potential medicine names", len(unique_names))
        return unique_names

    def _extract_prescription_info(
        self,
        text: str,
        sections: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Extract prescription/dosage information with priority on the “Comment prendre” section.
        """
        posology_block = ""
        if sections:
            posology_block = self._find_section(sections, ["comment prendre", "posologie"])

        source = posology_block or text
        relevant_lines: List[str] = []
        for line in source.splitlines():
            cleaned = line.strip()
            if len(cleaned) < 3:
                continue
            if re.search(r'\b(comprim|prise|heures?|mg|dose|posologie|kg)\b', cleaned, re.IGNORECASE):
                relevant_lines.append(cleaned)

        if not relevant_lines:
            return None

        prescription_info = " ".join(relevant_lines)
        self.logger.debug("Extracted prescription info length=%d", len(prescription_info))
        return prescription_info

    def _extract_fields(
        self,
        text: str,
        sections: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured fields from text and section blocks.
        """
        fields: Dict[str, Any] = {}

        composition_block = ""
        if sections:
            composition_block = self._find_section(
                sections,
                ["contenu de l'emballage", "autres informations", "ce que contient"]
            )

        reference_block = composition_block or text

        ingredient_pattern = re.compile(
            r'([A-Za-zÀ-ÖØ-öø-ÿ\'\- ]+)\.{2,}\s*(\d+(?:[.,]\d+)?)\s*(mg|g|ml|µg)',
            re.IGNORECASE
        )
        ingredient_matches = ingredient_pattern.findall(reference_block)
        if ingredient_matches:
            fields["active_ingredients_with_dosage"] = [
                f"{name.strip()}: {amount.replace(',', '.')} {unit}"
                for name, amount, unit in ingredient_matches
            ]
            fields["active_ingredient"] = ingredient_matches[0][0].strip()

        excipient_match = re.search(
            r'Les autres composants sont\s*:([^\n]+(?:\n(?!\s*\n)[^\n]+)*)',
            reference_block,
            re.IGNORECASE
        )
        if excipient_match:
            raw_excipients = excipient_match.group(1)
            # Remove metadata labels that appear with the list
            raw_excipients = re.sub(
                r'(?:a effet notoire|Liste des excipients|ayant effet notoire)[:\s]*',
                '',
                raw_excipients,
                flags=re.IGNORECASE
            )
            excipients_list = self._clean_list_string(raw_excipients)
            # Filter out empty or metadata-only items
            excipients_list = [e for e in excipients_list if e and len(e) > 2 and e.lower() != "liste"]
            if excipients_list:
                fields["excipients"] = excipients_list

        # Extract pharmaceutical form
        form_match = re.search(
            r'(?:forme\s+pharmaceutique|se\s+présente\s+sous\s+forme\s+de)\s*[:\s]*([^\n.]+)',
            reference_block,
            re.IGNORECASE
        )
        if form_match:
            form_text = form_match.group(1).strip()
            # Remove question markers and extra text
            form_text = re.sub(r'^\s*[?!]+\s*', '', form_text)
            form_text = re.sub(r'\s+(?:et|ou|ainsi)', ' ', form_text, flags=re.IGNORECASE)
            if form_text:
                fields["pharmaceutical_form"] = form_text

        indications_block = self._find_section(
            sections or {},
            ["qu'est-ce que", "quest-ce que"]
        )
        if indications_block:
            # Filter out question headers and extract only relevant content
            lines = []
            for line in indications_block.splitlines():
                cleaned = line.strip()
                if (cleaned and len(cleaned) > 3 and
                    not re.match(
                        r'^(Ce médicament|Est-ce que|QUE|ET DANS|EST-IL|indiqué|Classe)',
                        cleaned,
                        re.IGNORECASE
                    )):
                    lines.append(cleaned)
            if lines:
                indication_summary = " ".join(lines[:5])
                fields["indications"] = indication_summary

        safety_block = self._find_section(
            sections or {},
            ["quelles sont les informations", "contre-indications", "avertissements"]
        )
        if safety_block:
            contra_match = re.search(
                r'Ne prenez jamais[^:]*:(.+?)(?:\n\s*\n|$)',
                safety_block,
                re.IGNORECASE | re.DOTALL
            )
            if contra_match:
                fields["contraindications"] = self._clean_list_block(contra_match.group(1))

        side_effects_block = self._find_section(sections or {}, ["quels sont les effets indésirables"])
        if side_effects_block:
            fields["side_effects"] = self._clean_list_block(side_effects_block)

        storage_block = self._find_section(sections or {}, ["comment conserver", "conditions de conservation"])
        if storage_block:
            # Filter out instructional text and headers
            lines = []
            for line in storage_block.splitlines():
                cleaned = line.strip()
                if (cleaned and len(cleaned) > 3 and
                    not re.match(
                        r'^(COMMENT|Comment|Instructions|Tenir|Si|Les médicaments|Date de|Ne pas)',
                        cleaned,
                        re.IGNORECASE
                    )):
                    lines.append(cleaned)
            if lines:
                storage_summary = " ".join(lines[:4])
                fields["storage"] = storage_summary

        posology_block = self._find_section(sections or {}, ["comment prendre", "posologie"])
        if posology_block:
            fields["posology"] = self._summarize_section(posology_block, max_lines=8)

        self.logger.debug("Extracted %d structured fields", len(fields))
        return fields

    def _extract_manufacturer_info(
        self,
        text: str,
        sections: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Extract manufacturer, holder, and fabrication information.
        """
        info: Dict[str, str] = {}
        block = self._find_section(
            sections or {},
            ["contenu de l'emballage", "autres informations", "titulaire", "fabricant"]
        ) or text

        titulaire_pattern = re.compile(
            r'Titulaire de l[’\'`]autorisation de mise sur le marché\s*([^\n]+)',
            re.IGNORECASE
        )
        exploitant_pattern = re.compile(
            r'Exploitant de l[’\'`]autorisation de mise sur le marché\s*([^\n]+)',
            re.IGNORECASE
        )
        fabricant_pattern = re.compile(
            r'Fabricant\s*([^\n]+)',
            re.IGNORECASE
        )

        titulaire_match = titulaire_pattern.search(block)
        if titulaire_match:
            info["license_holder"] = titulaire_match.group(1).strip()

        exploitant_match = exploitant_pattern.search(block)
        if exploitant_match:
            info["operator"] = exploitant_match.group(1).strip()

        fabricant_match = fabricant_pattern.search(block)
        if fabricant_match:
            info["manufacturer"] = fabricant_match.group(1).strip()

        self.logger.debug("Extracted manufacturer info keys: %s", list(info.keys()))
        return info

    def _extract_regulatory_info(self, text: str) -> Dict[str, str]:
        """
        Extract regulatory information (AMM, ANSM references).
        """
        info: Dict[str, str] = {}
        amm_pattern = re.compile(r'(?:AMM|authorisation|approval)\s*[:\-–]\s*([^\n]+)', re.IGNORECASE)
        date_pattern = re.compile(r'(?:Mis à jour le|Updated on)\s*[:\-–]\s*([0-9/.\-]+)', re.IGNORECASE)
        agency_pattern = re.compile(r'(ANSM|agence nationale [^\n]+)', re.IGNORECASE)

        amm_match = amm_pattern.search(text)
        if amm_match:
            info["amm_number"] = amm_match.group(1).strip()

        date_match = date_pattern.search(text)
        if date_match:
            info["revision_date"] = date_match.group(1).strip()

        agency_match = agency_pattern.search(text)
        if agency_match:
            info["regulatory_agency"] = agency_match.group(1).strip()

        return info

    def _clean_list_block(self, block: str) -> List[str]:
        lines = []
        for raw_line in block.splitlines():
            line = raw_line.strip(" -•\t")
            if line:
                lines.append(line)
        return lines

    def _clean_list_string(self, text: str) -> List[str]:
        parts = re.split(r'[,\n;]+', text)
        return [part.strip() for part in parts if part.strip()]
    
    def _is_section_header_or_instruction(self, text: str) -> bool:
        """
        Check if text looks like a section header, question, or instruction
        rather than actual content.
        """
        text_upper = text.upper()
        header_patterns = [
            r'^COMMENT\s+',
            r'^QUELS?\s+SONT',
            r'^QUELLES?\s+SONT',
            r'^DANS\s+QUELS?\s+CAS',
            r'^QU[E\'`]?EST[- ]CE\s+QUE',
            r'^LISTE\s+',
            r'^\d+\.\s+',
            r'^EN\s+CAS\s+DE',
            r'^INSTRUCTIONS?\s+',
            r'^VEUILLEZ\s+',
        ]
        return any(re.match(pattern, text_upper, re.IGNORECASE) for pattern in header_patterns)

    def _summarize_section(self, block: str, max_lines: int = 4) -> str:
        lines = [line.strip(" -•\t") for line in block.splitlines() if line.strip()]
        return " ".join(lines[:max_lines])

    def format_for_cleaner(self, extracted_data: ExtractedData) -> Dict[str, Any]:
        """
        Format extracted data for the cleaning/validation module.
        """
        return {
            "raw_text": extracted_data.raw_text,
            "extracted_fields": {
                "medicine_names": extracted_data.medicine_names,
                "prescription_info": extracted_data.prescription_info,
                **extracted_data.extracted_fields
            },
            "metadata": extracted_data.metadata,
            "ocr_confidence": extracted_data.metadata.get("ocr_confidence", 0.0)
        }

    def format_for_search(self, extracted_data: ExtractedData) -> Dict[str, Any]:
        """
        Format extracted data as search queries for search engine module.
        """
        queries = {
            "medicine_names": extracted_data.medicine_names,
            "primary_query": " ".join(extracted_data.medicine_names[:1]) if extracted_data.medicine_names else "",
            "alternative_queries": extracted_data.medicine_names[1:] if len(extracted_data.medicine_names) > 1 else [],
            "prescription_query": extracted_data.prescription_info or "",
            "full_text": extracted_data.raw_text
        }

        return {
            k: v for k, v in queries.items()
            if v and ((isinstance(v, str) and v.strip()) or (isinstance(v, list) and v))
        }

    def format_for_csv(
        self,
        extracted_data: ExtractedData,
        include_raw_text: bool = False
    ) -> Dict[str, Any]:
        """
        Flatten extracted data into a single row dictionary suitable for CSV output.
        """
        serialized = asdict(extracted_data)
        metadata = serialized.get("metadata") or {}
        fields = serialized.get("extracted_fields") or {}

        row: Dict[str, Any] = {
            "source_file": metadata.get("source_file", ""),
            "source_type": metadata.get("source_type", ""),
            "ocr_confidence": metadata.get("ocr_confidence", ""),
            "medicine_names": "; ".join(serialized.get("medicine_names") or []),
            "prescription_info": serialized.get("prescription_info") or "",
        }

        for key, value in fields.items():
            row[key] = self._flatten_value(value)

        if include_raw_text:
            row["raw_text"] = serialized.get("raw_text", "")

        return row

    def save_extracted_data_to_csv(
        self,
        data: Union[ExtractedData, List[ExtractedData]],
        csv_path: Union[str, Path],
        include_raw_text: bool = False,
        append: bool = False
    ) -> Path:
        """
        Format and persist one or many ExtractedData entries into a CSV file.

        Args:
            data: A single ExtractedData or a list of them.
            csv_path: Destination CSV path.
            include_raw_text: Include the raw OCR text column (disabled by default).
            append: Append to existing file if True; overwrite otherwise.

        Returns:
            Path to the written CSV file.
        """
        path = Path(csv_path)
        entries = data if isinstance(data, list) else [data]
        rows = [self.format_for_csv(entry, include_raw_text=include_raw_text) for entry in entries]

        file_exists = path.exists() and path.stat().st_size > 0
        mode = "a" if append and file_exists else "w"

        with path.open(mode, newline='', encoding='utf-8') as csv_file:
            fieldnames = sorted({key for row in rows for key in row.keys()})
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            if not file_exists or mode == "w":
                writer.writeheader()

            for row in rows:
                writer.writerow(row)

        self.logger.info("Saved %d extraction rows to %s", len(rows), path)
        return path

    def _flatten_value(self, value: Any) -> str:
        if isinstance(value, list):
            return " | ".join(str(item) for item in value if item is not None)
        if isinstance(value, dict):
            return " | ".join(f"{k}: {v}" for k, v in value.items())
        return str(value) if value is not None else ""