"""Very small OCR pipeline for images/PDFs with txt export."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .ocr_engine import OCREngine
from .processors.image_processor import ImageProcessor
from .processors.pdf_processor import PDFProcessor


class SimpleOCRPipeline:
    """Simple OCR pipeline: process image/pdf and save plain text results."""

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        enhance_quality: bool = True,
        pdf_dpi: int = 250,
    ) -> None:
        if languages is None:
            env_languages = __import__("os").environ.get("OCR_LANGUAGES", "fra")
            if "," in env_languages:
                languages = [item.strip() for item in env_languages.split(",") if item.strip()]
            else:
                languages = [item.strip() for item in env_languages.split("+") if item.strip()]

        # Fallback to English if languages unavailable
        if not languages:
            languages = ["eng"]

        self.ocr_engine = OCREngine(languages)
        self.image_processor = ImageProcessor(enhance_quality=enhance_quality)
        self.pdf_processor = PDFProcessor(dpi=pdf_dpi)

    def process_image(self, image_path: str) -> Dict[str, Any]:
        image = self.image_processor.process(image_path)
        ocr = self.ocr_engine.extract_text_with_confidence(image)
        confidence = float(ocr.get("confidence", 0.0) or 0.0)
        text = ocr.get("text", "")
        success = bool(text.strip()) or confidence > 0.0

        return {
            "success": success,
            "source_type": "image",
            "source_file": image_path,
            "text": text,
            "confidence": confidence,
            "languages": ocr.get("languages", []),
        }

    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        pages = self.pdf_processor.process(pdf_path)

        page_results: List[Dict[str, Any]] = []
        all_text: List[str] = []
        confidences: List[float] = []

        for page_number, image in enumerate(pages, start=1):
            ocr = self.ocr_engine.extract_text_with_confidence(image)
            page_text = ocr.get("text", "")
            page_confidence = float(ocr.get("confidence", 0.0) or 0.0)

            page_results.append(
                {
                    "page": page_number,
                    "text": page_text,
                    "confidence": page_confidence,
                }
            )

            if page_text:
                all_text.append(f"\n--- PAGE {page_number} ---\n{page_text}")
                confidences.append(page_confidence)

        return {
            "success": bool(all_text),
            "source_type": "pdf",
            "source_file": pdf_path,
            "page_count": len(pages),
            "average_confidence": (sum(confidences) / len(confidences)) if confidences else 0.0,
            "languages": self.ocr_engine.languages,
            "text": "\n".join(all_text).strip(),
            "pages": page_results,
        }

    def process_document(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            return self.process_pdf(file_path)
        return self.process_image(file_path)

    @staticmethod
    def save_result_txt(result: Dict[str, Any], output_path: str) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = [
            "Simple OCR Result",
            "=" * 60,
            f"Source: {result.get('source_file', '')}",
            f"Type: {result.get('source_type', '')}",
            f"Success: {result.get('success', False)}",
            f"Languages: {', '.join(result.get('languages', []))}",
            f"Confidence: {result.get('average_confidence', result.get('confidence', 0.0)):.2%}",
        ]

        if result.get("source_type") == "pdf":
            lines.append(f"Pages: {result.get('page_count', 0)}")
            lines.append("")
            lines.append("Page summary")
            lines.append("-" * 60)
            for page in result.get("pages", []):
                lines.append(f"Page {page.get('page')}: confidence={page.get('confidence', 0.0):.2%}")

        lines.extend([
            "",
            "Extracted text",
            "-" * 60,
            result.get("text", ""),
        ])

        output.write_text("\n".join(lines), encoding="utf-8")
        return output
