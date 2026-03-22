"""PaddleOCR Demo - Practical examples of using PaddleOCR."""

import os
import sys
import logging
import warnings
from pathlib import Path
from io import StringIO

# Set environment variable to disable model source check
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# Suppress all PaddleOCR and C++ backend output
os.environ['PADDLE_PDX_ENABLE_LOGGING'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('paddle').setLevel(logging.ERROR)
logging.getLogger('paddleocr').setLevel(logging.ERROR)
logging.getLogger('paddlex').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')

from src.paddle_ocr.paddle_engine import PaddleEngine
from src.paddle_ocr.paddle_pipeline import PaddleOCRPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def extract_from_image():
    """Extract text from an image file."""
    print("\n" + "="*60)
    print("Example 1: Extract Text from Image")
    print("="*60)
    
    engine = PaddleEngine(languages=["fr","ar"])
    image_path = r"static/test_1.jpg"
    result = engine.extract_text(image_path)
    
    if result['success']:
        output_path = Path("static") / "image_text_extracted_paddle_french.txt"
        output_lines = [
            "PaddleOCR Image Extraction Result",
            "=" * 60,
            f"Source image: {image_path}",
            f"Confidence: {result.get('confidence', 0.0):.2%}",
            f"Detected language: {result.get('language', 'unknown')}",
            f"Languages used: {', '.join(result.get('detected_languages', [])) or 'none'}",
            "",
        ]

        # Optional layout analysis (title/table/text regions)
        layout = engine.extract_layout(image_path)
        if layout.get("success"):
            blocks = layout.get("blocks", [])
            output_lines.extend([
                f"Layout detected: True",
                f"Layout blocks count: {len(blocks)}",
                "",
                "Layout Blocks",
                "-" * 60,
            ])

            for idx, block in enumerate(blocks, start=1):
                block_text = (block.get("text") or "").strip()
                preview = block_text.replace("\n", " ")[:200]
                output_lines.append(
                    f"[{idx}] type={block.get('type')} bbox={block.get('bbox')}"
                )
                if preview:
                    output_lines.append(f"    text: {preview}")
        else:
            output_lines.extend([
                "Layout detected: False",
                f"Layout error: {layout.get('error', 'unknown error')}",
            ])

        output_lines.extend([
            "",
            "Extracted Text",
            "-" * 60,
            result.get("text", ""),
        ])

        output_path.write_text("\n".join(output_lines), encoding="utf-8")

        print(f"[SUCCESS] Text extracted")
    else:
        print(f"[FAILED] {result.get('error', 'Unknown error')}")


def extract_from_pdf():
    """Extract text from a PDF document."""
    print("\n" + "="*60)
    print("Example 2: Extract Text from PDF")
    print("="*60)
    
    pipeline = PaddleOCRPipeline(paddle_engine=PaddleEngine())
    pdf_path = "static/test.pdf"
    result = pipeline.process_document(pdf_path)
    
    if result['success']:
        output_path = Path("static") / "pdf_test_extracted_paddle.txt"
        output_lines = [
            "PaddleOCR PDF Extraction Result",
            "=" * 60,
            f"Source PDF: {pdf_path}",
            f"Pages: {result.get('page_count', 'Unknown')}",
            f"Processed Pages: {result.get('processed_pages', 'Unknown')}",
            f"Average Confidence: {result.get('average_confidence', 0.0):.2%}",
            f"Layout detected: {result.get('layout_success', False)}",
            f"Layout blocks count: {len(result.get('layout_blocks', []))}",
            "",
            "Layout Blocks",
            "-" * 60,
        ]

        for idx, block in enumerate(result.get("layout_blocks", []), start=1):
            block_text = (block.get("text") or "").strip()
            preview = block_text.replace("\n", " ")[:200]
            output_lines.append(
                f"[{idx}] page={block.get('page')} type={block.get('type')} bbox={block.get('bbox')}"
            )
            if preview:
                output_lines.append(f"    text: {preview}")

        output_lines.extend([
            "",
            "Extracted Text",
            "-" * 60,
            result.get("text", ""),
        ])

        output_path.write_text("\n".join(output_lines), encoding="utf-8")

        print(f"[SUCCESS] PDF processed")
    else:
        print(f"[FAILED] {result.get('error', 'Unknown error')}")



def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("PaddleOCR - Practical Usage Examples")
    print("="*60)
    
    extract_from_image()
    # extract_from_pdf()

if __name__ == "__main__":
    main()
