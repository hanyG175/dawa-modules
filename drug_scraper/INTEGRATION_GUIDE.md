# Integration Guide for External Modules

This guide explains how to integrate your cleaning/validation and search engine modules with the OCR system when they're ready.

## Quick Start: Integrating Your Modules

### Step 1: Implement the Required Interface

When your module is ready, implement the appropriate interface:

#### For Data Cleaner Module:

```python
# in your_cleaner_module.py
from src.ocr import DataCleanerInterface, ExtractedData
from typing import Dict, Any

class YourDataCleaner(DataCleanerInterface):
    """Your implementation of data cleaning and validation."""
    
    def __init__(self):
        """Initialize your cleaner with any dependencies."""
        # Your initialization code
        pass
    
    def clean(self, data: ExtractedData) -> Dict[str, Any]:
        """
        Clean and structure extracted OCR data.
        
        Args:
            data: ExtractedData from OCR system containing:
                - raw_text: Original OCR extracted text
                - medicine_names: Extracted medicine names list
                - prescription_info: Dosage/administration info
                - extracted_fields: Dict of structured data
                - metadata: Processing metadata
        
        Returns:
            Cleaned data dictionary with your custom structure
            
        Example:
            {
                "drug_id": "ABC123",
                "name": "Aspirin",
                "dosage": "500mg",
                "manufacturer": "Pharma Corp",
                "status": "validated"
            }
        """
        # Your cleaning logic here
        # You can access any part of the extracted data:
        medicine_names = data.medicine_names
        prescription = data.prescription_info
        raw_text = data.raw_text
        fields = data.extracted_fields
        
        # Process and clean the data
        cleaned_data = {
            "raw_text": raw_text,
            "medicine_names": medicine_names,
            "prescription_info": prescription,
            "fields": fields,
            # Add your custom cleaned fields
        }
        
        return cleaned_data
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate cleaned data.
        
        Args:
            data: The dictionary returned by clean()
        
        Returns:
            True if data is valid and should be processed
            False if data should be skipped
        """
        # Your validation logic
        # Example checks:
        if not data.get("medicine_names"):
            return False
        
        if data.get("ocr_confidence", 0) < 0.5:
            return False
        
        return True
```

#### For Search Engine Module:

```python
# in your_search_module.py
from src.ocr import SearchEngineInterface
from typing import List, Dict, Any

class YourSearchEngine(SearchEngineInterface):
    """Your implementation of drug search engine."""
    
    def __init__(self):
        """Initialize your search engine with database connection, etc."""
        # Your initialization code
        # e.g., self.db = connect_to_database()
        pass
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        General search across all drug attributes.
        
        Args:
            query: Search query string
                   Can be medicine name, generic name, or any text
        
        Returns:
            List of matching drug records, each containing:
            {
                "id": "drug_id_123",
                "name": "Medicine Name",
                "active_ingredient": "...",
                "manufacturer": "...",
                "indication": "...",
                # ... other fields
                "confidence": 0.95  # Optional: your search confidence
            }
        """
        # Your search logic
        # Example:
        # results = self.db.search(query)
        # return results
        pass
    
    def search_by_medicine_name(self, medicine_name: str) -> List[Dict[str, Any]]:
        """
        Search specifically by medicine name.
        More precise than general search.
        
        Args:
            medicine_name: Exact or partial medicine name
        
        Returns:
            List of matching drug records (same format as search())
        """
        # Your specific search logic
        # Example:
        # return self.db.search_by_name(medicine_name)
        pass
```

### Step 2: Register Your Module with the Pipeline

```python
from src.ocr import StandardOCRPipeline
from your_cleaner_module import YourDataCleaner
from your_search_module import YourSearchEngine

# Initialize pipeline
pipeline = StandardOCRPipeline()

# Register your modules
pipeline.register_data_cleaner(YourDataCleaner())
pipeline.register_search_engine(YourSearchEngine())

# Now use the pipeline
cleaned_results = pipeline.process_and_clean("drug_notice.pdf")
search_results = pipeline.process_and_search("prescription.jpg")
```

### Step 3: Use with Your Integrated System

```python
# Use Case 1: Process drug notices with cleaning
pipeline = StandardOCRPipeline()
pipeline.register_data_cleaner(YourDataCleaner())

cleaned_results = pipeline.process_and_clean("drug_notice.pdf")
for cleaned_data in cleaned_results:
    # Store in your database
    db.insert_drug(cleaned_data)

# Use Case 2: Process user uploads with search
pipeline = StandardOCRPipeline()
pipeline.register_search_engine(YourSearchEngine())

search_results = pipeline.process_and_search("prescription.jpg")
for drug in search_results:
    # Display to user or save to user's medicine list
    user.add_medicine(drug)
```

## Data Flow Diagrams

### Use Case 1: Drug Notice Processing

```
User uploads PDF
     ↓
PDFProcessor: Convert to images
     ↓
OCREngine: Extract text from images
     ↓
DataExtractor: Structure data (names, dosage, etc.)
     ↓
YourDataCleaner.clean(): Clean and standardize
     ↓
YourDataCleaner.validate(): Ensure quality
     ↓
Database/Storage
```

**ExtractedData passed to your cleaner:**
```python
ExtractedData(
    medicine_names=["Aspirin", "Acetylsalicylic acid"],
    prescription_info="Dosage: 500mg | Administration: Oral, 2x daily",
    raw_text="Full OCR text from all pages...",
    extracted_fields={
        "active_ingredient": "Acetylsalicylic acid",
        "manufacturer": "Pharma Corp",
        "indications": ["Pain relief", "Anti-inflammatory"],
        "side_effects": ["Stomach upset", "Bleeding risk"],
        ...
    },
    metadata={
        "source_type": "pdf",
        "ocr_confidence": 0.94,
        "source_file": "drug_notice.pdf"
    }
)
```

### Use Case 2: User Upload Processing

```
User uploads image (prescription/medicine)
     ↓
ImageProcessor: Load and enhance quality
     ↓
OCREngine: Extract text
     ↓
DataExtractor: Extract medicine names and prescription
     ↓
YourSearchEngine.search_by_medicine_name(): Find matching drugs
     ↓
Return results to user
```

**Data passed to your search engine:**
```python
medicine_names = ["Paracetamol", "Acetaminophen"]
prescription_query = "Dosage: 500mg | Usage: Fever reduction"
full_text = "Complete OCR text from image"

# Your search method gets called:
results = search_engine.search_by_medicine_name("Paracetamol")
```

## Integration Checklist

- [ ] Implement `DataCleanerInterface` or `SearchEngineInterface`
- [ ] Test your module independently first
- [ ] Register your module with the pipeline
- [ ] Test end-to-end with sample PDFs/images
- [ ] Handle edge cases (empty results, errors, etc.)
- [ ] Add logging for debugging
- [ ] Set up error handling for database failures
- [ ] Optimize for production performance

## Testing During Integration

```python
from src.ocr import StandardOCRPipeline, MockDataCleaner
from your_cleaner_module import YourDataCleaner

# Test with mock first
mock_cleaner = MockDataCleaner()
pipeline = StandardOCRPipeline()
pipeline.register_data_cleaner(mock_cleaner)
results = pipeline.process_and_clean("test.pdf")
assert len(results) > 0

# Test with your real implementation
your_cleaner = YourDataCleaner()
pipeline.register_data_cleaner(your_cleaner)
results = pipeline.process_and_clean("test.pdf")
# Verify your custom cleaning was applied
```

## Common Integration Patterns

### Pattern 1: Direct Integration (Recommended)

```python
# Application code
pipeline = StandardOCRPipeline()
pipeline.register_data_cleaner(DataCleanerImpl())
pipeline.register_search_engine(SearchEngineImpl())

# Use the pipeline
results = pipeline.process_and_clean("notice.pdf")
```

### Pattern 2: Dependency Injection

```python
def setup_ocr_system(cleaner: DataCleanerInterface, 
                     engine: SearchEngineInterface) -> StandardOCRPipeline:
    pipeline = StandardOCRPipeline()
    pipeline.register_data_cleaner(cleaner)
    pipeline.register_search_engine(engine)
    return pipeline

# In your main app
pipeline = setup_ocr_system(
    DataCleanerImpl(),
    SearchEngineImpl()
)
```

### Pattern 3: Configuration-Based

```python
import importlib
from config import OCR_CONFIG

def load_ocr_system():
    pipeline = StandardOCRPipeline()
    
    # Load cleaner class from config
    cleaner_module = importlib.import_module(OCR_CONFIG['cleaner_module'])
    cleaner_class = getattr(cleaner_module, OCR_CONFIG['cleaner_class'])
    pipeline.register_data_cleaner(cleaner_class())
    
    # Load search engine class from config
    search_module = importlib.import_module(OCR_CONFIG['search_module'])
    search_class = getattr(search_module, OCR_CONFIG['search_class'])
    pipeline.register_search_engine(search_class())
    
    return pipeline
```

## Handling Errors

Your modules will be called by the pipeline, which handles some errors:

```python
class YourDataCleaner(DataCleanerInterface):
    def clean(self, data: ExtractedData) -> Dict[str, Any]:
        try:
            # Your logic
            return cleaned_data
        except Exception as e:
            logger.error(f"Cleaning failed: {e}")
            # Return minimal valid structure to allow graceful degradation
            return {"error": str(e), "raw_data": data.raw_text}
    
    def validate(self, data: Dict[str, Any]) -> bool:
        try:
            # Validation logic
            return True
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False  # Skip invalid data
```

## Performance Considerations

1. **Cache Results**: If you process the same PDFs multiple times
2. **Batch Processing**: Process multiple documents in parallel
3. **Index Database**: For search engine performance
4. **Connection Pooling**: If using database connections

## Support and Debugging

Enable detailed logging:

```python
import logging
from src.utils.logger import setup_logger

logger = setup_logger("ocr_system", log_level="DEBUG")

# All OCR operations will now log detailed information
pipeline = StandardOCRPipeline()
```

For issues, check:
1. Module implements the correct interface
2. All methods are implemented
3. Error handling is in place
4. Module is registered before use
5. Input data format matches expectations
