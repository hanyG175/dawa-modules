"""Simple demo for LayoutLM PDF extraction to txt."""

from pathlib import Path

from layoutLM import LayoutLMService


def main() -> None:
    pdf_path = Path("static/test.pdf")
    output_path = Path("static/test_layoutlm_output.txt")

    service = LayoutLMService()
    result = service.analyze_pdf(pdf_path, output_txt_path=output_path)

    print("[SUCCESS] LayoutLM PDF processed")
    print(f"Pages: {result.get('page_count', 0)}")
    print(f"Entities: {result.get('entity_count', 0)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
