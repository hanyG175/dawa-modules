import PIL
from PIL import Image
import pytesseract
import os
from src.ocr import StandardOCRPipeline
from src.ocr.processors.image_processor import ImageProcessor
from src.ocr.processors.pdf_processor import PDFProcessor
from src.ocr.data_extraction import DataExtractor
from matplotlib import pyplot as plt


pipeline = StandardOCRPipeline()
extractor = DataExtractor()

# Process image through cleaning pipeline
cleaned_results = pipeline.process_pdf("med.pdf")

# Export to CSV
print("\n" + "="*60)
print("EXPORTING TO CSV")
print("="*60)

try:
    # Export as flattened format (single row)
    csv_path = extractor.save_extracted_data_to_csv(cleaned_results, "ocr_results.csv")
    print(f"✓ Exported to {csv_path}")
    
    # Export with raw text included
    csv_path_text = extractor.save_extracted_data_to_csv(
        cleaned_results, 
        "ocr_results_with_text.csv",
        include_raw_text=True
    )
    print(f"✓ Exported (with raw text) to {csv_path_text}")
    
except Exception as e:
    print(f"✗ Error exporting to CSV: {e}")
#-------------------------------------------------------------------------
# # Image comaprision original vs processed
# original_image =  Image.open("Screenshot 2025-12-12 234708.png")

# processed_image = ImageProcessor(enhance_quality=True).process("Screenshot 2025-12-12 234708.png")
# image = ImageProcessor(enhance_quality=True).process("Screenshot 2025-12-12 234708.png")

# fig, axes = plt.subplots(1, 2, figsize=(12, 5))
# axes[0].imshow(original_image)
# axes[0].set_title('Original Image')
# axes[0].axis('off')
# axes[1].imshow(image)
# axes[1].set_title('Processed Image')
# axes[1].axis('off')
# plt.show()

#------------------------------------------------------
# Testing the PDF processor

# pdf_processor = PDFProcessor(dpi=300)
# pdf_images = pdf_processor.process("med.pdf")
# print(f"Extracted {len(pdf_images)} pages from PDF.")


# fig, axes = plt.subplots(1, 2, figsize=(12, 5))
# axes[0].imshow(pdf_images[0])  # Show the first page as original
# axes[0].set_title('1st Page of PDF')
# axes[0].axis('off')
# axes[1].imshow(pdf_images[-1])
# axes[1].set_title('Last Page of PDF')
# axes[1].axis('off')
# plt.show()