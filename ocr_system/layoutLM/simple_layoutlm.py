"""Simple LayoutLMv3 wrapper for image/PDF document entity extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pytesseract
from PIL import Image
from pytesseract import Output

from src.ocr.processors.pdf_processor import PDFProcessor


class LayoutLMService:
    """Minimal LayoutLM service with OCR + token classification."""

    def __init__(
        self,
        model_name: str = "microsoft/layoutlmv3-base",
        use_gpu: bool = False,
    ) -> None:
        import torch
        from transformers import AutoModel, AutoModelForTokenClassification, AutoProcessor

        self.model_name = model_name
        self.device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
        self._torch = torch
        self.task_mode = "token-classification"
        self.pdf_processor = PDFProcessor()

        self.processor = AutoProcessor.from_pretrained(model_name, apply_ocr=False)
        if model_name.strip().lower() == "microsoft/layoutlmv3-base":
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
            self.task_mode = "base"
        else:
            self.model = AutoModelForTokenClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def analyze_image(self, image_input: Union[str, Path, Image.Image]) -> Dict[str, Any]:
        """Run LayoutLM token classification on a single image."""
        image = self._to_pil_image(image_input)
        words, boxes = self._ocr_words_and_boxes(image)

        if not words:
            return {"success": False, "error": "No OCR words detected.", "entities": [], "words": []}

        encoding = self.processor(
            image,
            words,
            boxes=boxes,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        encoding = {k: v.to(self.device) for k, v in encoding.items()}

        entities: List[Dict[str, Any]] = []
        labeled_entities: List[Dict[str, Any]] = []

        if self.task_mode == "token-classification":
            with self._torch.no_grad():
                logits = self.model(**encoding).logits

            pred_ids = logits.argmax(-1).squeeze(0).tolist()
            word_ids = self.processor.tokenizer.word_ids(batch_index=0)

            used_word_ids = set()
            for token_index, word_index in enumerate(word_ids):
                if word_index is None or word_index in used_word_ids:
                    continue
                used_word_ids.add(word_index)

                label_id = pred_ids[token_index]
                label = self.model.config.id2label.get(label_id, "O")
                text = words[word_index]

                entities.append(
                    {
                        "text": text,
                        "label": label,
                        "bbox": boxes[word_index],
                    }
                )

            labeled_entities = [item for item in entities if item["label"] != "O"]
        else:
            # Base model has no token classification head.
            # Return OCR words as neutral entities so output file still contains structured data.
            with self._torch.no_grad():
                _ = self.model(**encoding)

            entities = [
                {
                    "text": words[idx],
                    "label": "WORD",
                    "bbox": boxes[idx],
                }
                for idx in range(len(words))
            ]
            labeled_entities = entities

        return {
            "success": True,
            "model": self.model_name,
            "mode": self.task_mode,
            "entities": labeled_entities,
            "words": entities,
            "word_count": len(words),
            "entity_count": len(labeled_entities),
        }

    def analyze_pdf(self, pdf_path: Union[str, Path], output_txt_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Run analysis page by page for a PDF and optionally save to txt."""
        pdf_path = Path(pdf_path)
        pages = self.pdf_processor.process(str(pdf_path))

        page_results: List[Dict[str, Any]] = []
        all_entities: List[Dict[str, Any]] = []

        for page_idx, page_image in enumerate(pages, start=1):
            result = self.analyze_image(page_image)
            result["page"] = page_idx
            page_results.append(result)

            for entity in result.get("entities", []):
                entity_with_page = dict(entity)
                entity_with_page["page"] = page_idx
                all_entities.append(entity_with_page)

        final_result: Dict[str, Any] = {
            "success": True,
            "source": str(pdf_path),
            "model": self.model_name,
            "mode": self.task_mode,
            "page_count": len(pages),
            "pages": page_results,
            "entities": all_entities,
            "entity_count": len(all_entities),
        }

        if output_txt_path is not None:
            self.save_result_txt(final_result, output_txt_path)

        return final_result

    def save_result_txt(self, result: Dict[str, Any], output_path: Union[str, Path]) -> Path:
        """Save structured analysis result into a plain txt file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = [
            "LayoutLM Extraction Result",
            "=" * 60,
            f"Source: {result.get('source', 'image')}",
            f"Model: {result.get('model', '')}",
            f"Mode: {result.get('mode', '')}",
            f"Pages: {result.get('page_count', 1)}",
            f"Entities: {result.get('entity_count', 0)}",
            "",
            "Entities",
            "-" * 60,
        ]

        for idx, entity in enumerate(result.get("entities", []), start=1):
            lines.append(
                f"[{idx}] page={entity.get('page', 1)} label={entity.get('label')} text={entity.get('text')} bbox={entity.get('bbox')}"
            )

        lines.append("")
        lines.append("Per-page details")
        lines.append("-" * 60)

        for page in result.get("pages", []):
            lines.append(
                f"Page {page.get('page')}: words={page.get('word_count', 0)} entities={page.get('entity_count', 0)}"
            )

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    @staticmethod
    def _to_pil_image(image_input: Union[str, Path, Image.Image]) -> Image.Image:
        if isinstance(image_input, Image.Image):
            return image_input.convert("RGB")
        return Image.open(str(image_input)).convert("RGB")

    @staticmethod
    def _ocr_words_and_boxes(image: Image.Image) -> Tuple[List[str], List[List[int]]]:
        width, height = image.size
        data = pytesseract.image_to_data(image, output_type=Output.DICT)

        words: List[str] = []
        boxes: List[List[int]] = []

        total_items = len(data.get("text", []))
        for i in range(total_items):
            text = (data["text"][i] or "").strip()
            conf = data.get("conf", ["-1"])[i]

            try:
                conf_value = float(conf)
            except (TypeError, ValueError):
                conf_value = -1

            if not text or conf_value < 0:
                continue

            left = int(data["left"][i])
            top = int(data["top"][i])
            w = int(data["width"][i])
            h = int(data["height"][i])

            x0 = int(1000 * left / max(width, 1))
            y0 = int(1000 * top / max(height, 1))
            x1 = int(1000 * (left + w) / max(width, 1))
            y1 = int(1000 * (top + h) / max(height, 1))

            words.append(text)
            boxes.append([x0, y0, x1, y1])

        return words, boxes
