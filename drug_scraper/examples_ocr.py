"""
Usage examples for the OCR system.
Demonstrates both use cases: drug notices and user uploads.
"""

import logging
from pathlib import Path

from src.ocr import (
    StandardOCRPipeline,
    MockDataCleaner,
    MockSearchEngine,
)
from src.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__, log_level="INFO")


def example_1_process_pdf_notices():
    """
    USE CASE 1: Processing scraped drug notices (PDFs)
    
    Workflow:
    1. Load PDF drug notice
    2. Extract text and structure
    3. Send to cleaning/validation module
    4. Store cleaned data
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: Processing Drug Notices (PDF)")
    logger.info("=" * 60)
    
    # Initialize pipeline
    pipeline = StandardOCRPipeline()
    
    # Register the data cleaner (mock for now, replace with real later)
    cleaner = MockDataCleaner()
    pipeline.register_data_cleaner(cleaner)
    
    # Example PDF path
    pdf_path = "data/raw/drug_notice.pdf"  # Replace with actual path
    
    # Check if file exists for demo
    if not Path(pdf_path).exists():
        logger.warning(f"Demo file not found: {pdf_path}")
        logger.info("Showing how to use the system:")
        logger.info(f"  1. pipeline = StandardOCRPipeline()")
        logger.info(f"  2. pipeline.register_data_cleaner(YourCleanerModule())")
        logger.info(f"  3. results = pipeline.process_and_clean('{pdf_path}')")
        logger.info(f"  4. for cleaned_data in results:")
        logger.info(f"         # Process cleaned data (save to DB, etc.)")
        return
    
    try:
        # Process PDF with cleaning
        cleaned_results = pipeline.process_and_clean(pdf_path)
        
        # Store or process cleaned data
        for page_num, cleaned_data in enumerate(cleaned_results, 1):
            logger.info(f"\nPage {page_num} Results:")
            logger.info(f"  Medicine Names: {cleaned_data.get('medicine_names', [])}")
            logger.info(f"  Prescription Info: {cleaned_data.get('prescription_info', 'N/A')}")
            logger.info(f"  OCR Confidence: {cleaned_data.get('ocr_confidence', 0.0):.2%}")
            
            # TODO: Here you would save to database or process further
            # db.insert_drug_notice(cleaned_data)
        
        logger.info(f"\n✓ Successfully processed {len(cleaned_results)} pages")
    
    except Exception as e:
        logger.error(f"✗ Error processing PDF: {str(e)}")


def example_2_process_user_upload():
    """
    USE CASE 2: Processing user uploads (prescriptions/medicine photos)
    
    Workflow:
    1. User uploads image (prescription, medicine bottle, etc.)
    2. Extract medicine name/prescription text
    3. Search for drug in database
    4. Return results to user
    """
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 2: Processing User Uploads (Image)")
    logger.info("=" * 60)
    
    # Initialize pipeline
    pipeline = StandardOCRPipeline()
    
    # Register the search engine (mock for now, replace with real later)
    search_engine = MockSearchEngine()
    pipeline.register_search_engine(search_engine)
    
    # Example image path
    image_path = "data/raw/user_prescription.jpg"  # Replace with actual path
    
    # Check if file exists for demo
    if not Path(image_path).exists():
        logger.warning(f"Demo file not found: {image_path}")
        logger.info("Showing how to use the system:")
        logger.info(f"  1. pipeline = StandardOCRPipeline()")
        logger.info(f"  2. pipeline.register_search_engine(YourSearchEngine())")
        logger.info(f"  3. results = pipeline.process_and_search('{image_path}')")
        logger.info(f"  4. for drug in results:")
        logger.info(f"         # Display drug info to user")
        return
    
    try:
        # Process image with search
        drug_results = pipeline.process_and_search(image_path)
        
        # Display results to user
        if drug_results:
            logger.info(f"\nFound {len(drug_results)} drug(s):\n")
            for drug in drug_results:
                logger.info(f"  Name: {drug.get('name', 'N/A')}")
                logger.info(f"  ID: {drug.get('id', 'N/A')}")
                logger.info(f"  Active Ingredient: {drug.get('active_ingredient', 'N/A')}")
                logger.info(f"  Indication: {drug.get('indication', 'N/A')}")
                logger.info(f"  Confidence: {drug.get('confidence', 0.0):.2%}")
                logger.info("")
        else:
            logger.info("✓ No drugs found matching the prescription")
        
    except Exception as e:
        logger.error(f"✗ Error processing image: {str(e)}")


def example_3_pdf_direct_processing():
    """
    ADVANCED: Direct PDF processing without integration modules
    
    Use this when you only need text extraction,
    without needing to integrate with cleaner or search yet.
    """
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 3: Direct PDF Processing (Text Only)")
    logger.info("=" * 60)
    
    # Initialize pipeline
    pipeline = StandardOCRPipeline()
    
    pdf_path = "data/raw/drug_notice.pdf"
    
    if not Path(pdf_path).exists():
        logger.warning(f"Demo file not found: {pdf_path}")
        logger.info("Showing how to use the system:")
        logger.info(f"  extracted_data_list = pipeline.process_pdf('{pdf_path}')")
        logger.info(f"  for extracted in extracted_data_list:")
        logger.info(f"      print(extracted.raw_text)  # Raw OCR text")
        logger.info(f"      print(extracted.medicine_names)  # Extracted names")
        logger.info(f"      print(extracted.extracted_fields)  # Structured data")
        return
    
    try:
        # Process PDF
        extracted_data_list = pipeline.process_pdf(pdf_path)
        
        for page_num, extracted in enumerate(extracted_data_list, 1):
            logger.info(f"\nPage {page_num}:")
            logger.info(f"  Raw Text Length: {len(extracted.raw_text)} characters")
            logger.info(f"  Medicine Names Found: {extracted.medicine_names}")
            logger.info(f"  Prescription Info: {extracted.prescription_info}")
            logger.info(f"  Extracted Fields: {list(extracted.extracted_fields.keys())}")
        
    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")


def example_4_image_direct_processing():
    """
    ADVANCED: Direct image processing without integration modules
    
    Use this when you only need text extraction,
    without needing to search yet.
    """
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 4: Direct Image Processing (Text Only)")
    logger.info("=" * 60)
    
    # Initialize pipeline
    pipeline = StandardOCRPipeline()
    
    image_path = "data/raw/medicine_scan.jpg"
    
    if not Path(image_path).exists():
        logger.warning(f"Demo file not found: {image_path}")
        logger.info("Showing how to use the system:")
        logger.info(f"  extracted = pipeline.process_image('{image_path}')")
        logger.info(f"  print(extracted.raw_text)  # Raw OCR text")
        logger.info(f"  print(extracted.medicine_names)  # Extracted names")
        return
    
    try:
        # Process image
        extracted = pipeline.process_image(image_path)
        
        logger.info(f"Raw Text:\n{extracted.raw_text}")
        logger.info(f"\nExtracted Medicine Names: {extracted.medicine_names}")
        logger.info(f"Prescription Info: {extracted.prescription_info}")
        logger.info(f"Extracted Fields: {extracted.extracted_fields}")
        
    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")


def example_5_component_usage():
    """
    ADVANCED: Using individual components
    
    For fine-grained control or custom workflows.
    """
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 5: Using Individual Components")
    logger.info("=" * 60)
    
    from src.ocr import (
        OCREngine,
        PDFProcessor,
        ImageProcessor,
        DataExtractor,
    )
    
    logger.info("\nComponent 1: OCREngine")
    logger.info("  ocr = OCREngine(languages=['eng', 'fra'])")
    logger.info("  result = ocr.extract_text(image)")
    
    logger.info("\nComponent 2: PDFProcessor")
    logger.info("  pdf_proc = PDFProcessor(dpi=300)")
    logger.info("  images = pdf_proc.process('document.pdf')")
    
    logger.info("\nComponent 3: ImageProcessor")
    logger.info("  img_proc = ImageProcessor(enhance_quality=True)")
    logger.info("  image = img_proc.process('scan.jpg')")
    
    logger.info("\nComponent 4: DataExtractor")
    logger.info("  extractor = DataExtractor()")
    logger.info("  data = extractor.extract_from_ocr_result(ocr_result)")
    
    logger.info("\nWorkflow Example:")
    logger.info("  1. pdf_proc = PDFProcessor()")
    logger.info("  2. images = pdf_proc.process('drug_notice.pdf')")
    logger.info("  3. ocr = OCREngine()")
    logger.info("  4. for image in images:")
    logger.info("         ocr_result = ocr.extract_text(image)")
    logger.info("         extractor = DataExtractor()")
    logger.info("         data = extractor.extract_from_ocr_result(ocr_result)")


if __name__ == "__main__":
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 58 + "║")
    logger.info("║" + "  OCR SYSTEM - USAGE EXAMPLES".center(58) + "║")
    logger.info("║" + " " * 58 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    
    # Run examples
    example_1_process_pdf_notices()
    example_2_process_user_upload()
    example_3_pdf_direct_processing()
    example_4_image_direct_processing()
    example_5_component_usage()
    
    logger.info("\n" + "=" * 60)
    logger.info("Examples completed!")
    logger.info("=" * 60)
