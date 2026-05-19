from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable

from .GoogleOCR import GoogleOCR

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS


@dataclass
class OCRResult:
    file_name: str
    file_type: str
    text: str
    characters: int
    words: int
    success: bool
    error: str | None = None


class GoogleDriveOCRModule:
    """Wrapper around GoogleOCR with image/PDF support."""

    def __init__(self, ocr_engine: GoogleOCR | None = None):
        self.ocr_engine = ocr_engine or GoogleOCR()

    def _build_result(self, file_name: str, extension: str, text: str) -> OCRResult:
        words = len(text.split()) if text else 0
        return OCRResult(
            file_name=file_name,
            file_type="pdf" if extension in SUPPORTED_PDF_EXTENSIONS else "image",
            text=text,
            characters=len(text),
            words=words,
            success=True,
            error=None,
        )

    def extract_from_bytes(self, file_name: str, payload: bytes) -> OCRResult:
        extension = Path(file_name).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            return OCRResult(
                file_name=file_name,
                file_type="unknown",
                text="",
                characters=0,
                words=0,
                success=False,
                error=f"Unsupported file type: {extension or 'no extension'}",
            )

        temp_input = None
        temp_output = None
        try:
            with NamedTemporaryFile(delete=False, suffix=extension) as tmp:
                temp_input = Path(tmp.name)
                tmp.write(payload)

            temp_output = Path(self.ocr_engine.run(str(temp_input)))
            text = temp_output.read_text(encoding="utf-8", errors="ignore")
            return self._build_result(file_name=file_name, extension=extension, text=text)
        except Exception as exc:
            return OCRResult(
                file_name=file_name,
                file_type="pdf" if extension in SUPPORTED_PDF_EXTENSIONS else "image",
                text="",
                characters=0,
                words=0,
                success=False,
                error=str(exc),
            )
        finally:
            if temp_input and temp_input.exists():
                try:
                    temp_input.unlink(missing_ok=True)
                except OSError:
                    pass
            if temp_output and temp_output.exists():
                try:
                    temp_output.unlink(missing_ok=True)
                except OSError:
                    pass

    def extract_batch_pdfs(self, files: Iterable[tuple[str, bytes]]) -> list[OCRResult]:
        results: list[OCRResult] = []
        for file_name, payload in files:
            extension = Path(file_name).suffix.lower()
            if extension not in SUPPORTED_PDF_EXTENSIONS:
                results.append(
                    OCRResult(
                        file_name=file_name,
                        file_type="pdf",
                        text="",
                        characters=0,
                        words=0,
                        success=False,
                        error="Batch mode supports PDF only.",
                    )
                )
                continue
            results.append(self.extract_from_bytes(file_name=file_name, payload=payload))
        return results
