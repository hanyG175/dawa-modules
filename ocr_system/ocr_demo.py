"""Simple OCR demo: process image/pdf and save txt outputs."""

from pathlib import Path
import os

from src.ocr import SimpleOCRPipeline


def _load_local_env(env_path: Path) -> None:
	"""Load key=value pairs from a small local .env file if present."""
	if not env_path.exists():
		return

	for line in env_path.read_text(encoding="utf-8").splitlines():
		stripped = line.strip()
		if not stripped or stripped.startswith("#") or "=" not in stripped:
			continue
		key, value = stripped.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		if key and key not in os.environ:
			os.environ[key] = value


def main() -> None:
	_load_local_env(Path("src/ocr/.env"))
	print("Loaded OCR_LANGUAGES:", os.environ.get("OCR_LANGUAGES", "(not set)"))
	print("Loaded TESSDATA_PREFIX:", os.environ.get("TESSDATA_PREFIX", "(not set)"))
	print()

	pipeline = SimpleOCRPipeline(languages=["fra"])

	image_input = "static/test_1.jpg"
	image_result = pipeline.process_image(image_input)
	image_output = pipeline.save_result_txt(image_result, "static/test_2_ocr.txt")

	print("[IMAGE]")
	print(f"Success: {image_result.get('success')}")
	print(f"Confidence: {image_result.get('confidence', 0.0):.2%}")
	print(f"Saved: {image_output}")

	# pdf_input = "static/test.pdf"
	# pdf_result = pipeline.process_document(pdf_input)
	# pdf_output = pipeline.save_result_txt(pdf_result, "static/test_pdf_ocr_1.txt")

	# print("\n[PDF]")
	# print(f"Success: {pdf_result.get('success')}")
	# print(f"Pages: {pdf_result.get('page_count', 0)}")
	# print(f"Avg confidence: {pdf_result.get('average_confidence', 0.0):.2%}")
	# print(f"Saved: {pdf_output}")


if __name__ == "__main__":
	main()
