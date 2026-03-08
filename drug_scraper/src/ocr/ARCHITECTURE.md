# OCR System Architecture

## System Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OCR SYSTEM ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────┘

USE CASE 1: Drug Notices                    USE CASE 2: User Uploads
─────────────────────────────────────────────────────────────────────────────

    PDF File                                    Image File
       │                                            │
       ├─────────────────────────┬─────────────────┤
       │                         │                 │
       ▼                         ▼                 ▼
   PDFProcessor             ImageProcessor    ImageProcessor
   ├─ Validation            ├─ Validation     ├─ Validation
   ├─ PDF→Images           ├─ Enhancement    ├─ Enhancement
   └─ 300 DPI              ├─ Denoising      ├─ Denoising
                           └─ PIL Image      └─ PIL Image
       │                         │                 │
       └─────────────────────────┴─────────────────┘
                                 │
                                 ▼
                            OCREngine
                         (Tesseract-based)
                         ├─ Multi-language
                         ├─ Confidence scores
                         └─ Extract text
                                 │
                                 ▼
                            OCRResult
                         ├─ raw_text
                         ├─ confidence
                         └─ metadata
                                 │
                                 ▼
                           DataExtractor
                         ├─ Medicine names
                         ├─ Dosage/Rx info
                         ├─ Structured fields
                         └─ Format conversion
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
           ExtractedData                   ExtractedData
           (Structured)                    (Structured)
                │                                 │
    ┌───────────┴────────────┐      ┌────────────┴────────┐
    │                        │      │                     │
    ▼                        ▼      ▼                     ▼
YourDataCleaner         [Store]  SearchEngine        [UI Display]
├─ clean()                │      ├─ search()
├─ validate()             │      └─ search_by_name()
└─ Custom logic           │                 │
    │                     │                 ▼
    ▼                     │            Results
Cleaned Data              │          ├─ Drug info
├─ Validation             │          ├─ Dosage
├─ Standardization        │          ├─ Indications
└─ Ready for DB           ▼          └─ Confidence
                       Database
```

## Component Relationships

```
┌──────────────────────────────────────────────────────────────┐
│                    StandardOCRPipeline                       │
│  (Main orchestrator - coordinates all components)            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │               Document/Image Processing                 │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │  PDFProcessor (dpi: 150/300/600)                        │ │
│  │  ImageProcessor (enhance: True/False)                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                     │
│                          ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   OCR Processing                         │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │  OCREngine (languages: ['eng', 'fra', ...])            │ │
│  │  Tesseract integration                                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                     │
│                          ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Data Extraction                          │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │  DataExtractor (pattern matching, field extraction)    │ │
│  │  ExtractedData (structured output)                      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                     │
│              ┌───────────┴───────────┐                        │
│              │                       │                        │
│              ▼                       ▼                        │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │  DataCleaner         │  │  SearchEngine                │ │
│  │  [Optional]          │  │  [Optional]                  │ │
│  │  - clean()           │  │  - search()                  │ │
│  │  - validate()        │  │  - search_by_medicine_name()│ │
│  └──────────────────────┘  └──────────────────────────────┘ │
│              │                       │                        │
│              ▼                       ▼                        │
│           Cleaned              Search Results                │
│          Data Dict             Drug Records                  │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow: Use Case 1 (Drug Notices)

```
User/System
    │
    │ Uploads PDF
    ▼
┌─────────────────┐
│  PDF File       │
│  drug_notice.pdf│
└────────┬────────┘
         │
         ▼
    ┌──────────────────────────────┐
    │   PDFProcessor               │
    │  (convert to images)         │
    │  ✓ Validates format          │
    │  ✓ Checks file size          │
    │  ✓ Converts @ DPI            │
    └────────┬─────────────────────┘
             │
             ▼
    [Image, Image, Image, ...]  (one per page)
             │
             ├─────────────────────────┐
             │                         │
             ▼                         ▼
    ┌──────────────────┐     ┌──────────────────┐
    │ ImageProcessor   │     │ ImageProcessor   │
    │ (enhance)        │     │ (enhance)        │
    └────────┬─────────┘     └────────┬─────────┘
             │                        │
             ▼                        ▼
    ┌──────────────────┐     ┌──────────────────┐
    │ OCREngine        │     │ OCREngine        │
    │ (extract text)   │     │ (extract text)   │
    └────────┬─────────┘     └────────┬─────────┘
             │                        │
             ▼                        ▼
    ┌──────────────────────────────────────────┐
    │ OCRResult (for each page)                 │
    │ ├─ raw_text: "..."                       │
    │ ├─ confidence: 0.94                       │
    │ ├─ source_type: "pdf"                     │
    │ └─ metadata: {page: 1, ...}               │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ DataExtractor                             │
    │ (structure the data)                      │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ ExtractedData (for each page)             │
    │ ├─ medicine_names: ["Aspirin", ...]      │
    │ ├─ prescription_info: "500mg, 2x daily"  │
    │ ├─ extracted_fields: {...}               │
    │ └─ metadata: {...}                        │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ YourDataCleaner.clean()                   │
    │ (clean & standardize)                     │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ YourDataCleaner.validate()                │
    │ (ensure quality)                          │
    └────────┬─────────────────────────────────┘
             │
        ┌────┴────┐
        │          │
      ✓ Valid   ✗ Invalid
        │          │
        ▼          ▼
    Database    [Skip]
```

## Data Flow: Use Case 2 (User Uploads)

```
User
  │
  │ Uploads prescription/medicine image
  ▼
┌──────────────────┐
│ Image File       │
│ prescription.jpg │
└────────┬─────────┘
         │
         ▼
    ┌──────────────────────────────┐
    │ ImageProcessor               │
    │ (load & enhance)             │
    │ ✓ Validates format/size      │
    │ ✓ Denoises image             │
    │ ✓ Enhances contrast          │
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ OCREngine        │
    │ (extract text)   │
    │ Tesseract        │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ OCRResult                                 │
    │ ├─ raw_text: "Paracetamol 500mg"         │
    │ ├─ confidence: 0.92                       │
    │ └─ metadata: {...}                        │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ DataExtractor                             │
    │ (extract medicine names & rx info)        │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ ExtractedData                             │
    │ ├─ medicine_names: ["Paracetamol"]       │
    │ ├─ prescription_info: "500mg, fever..."  │
    │ └─ metadata: {...}                        │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ YourSearchEngine.search_by_medicine_name()│
    │ ("Paracetamol")                           │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ Drug Results (List)                       │
    │ ├─ {id: "123", name: "Paracetamol", ...} │
    │ ├─ {id: "456", name: "Acetaminophen",..} │
    │ └─ ...                                    │
    └────────┬─────────────────────────────────┘
             │
             ▼
         UI/API
      Display to User
```

## Class Hierarchy

```
BaseProcessor (abstract)
├── PDFProcessor
│   ├─ validate_input()
│   └─ process()
└── ImageProcessor
    ├─ validate_input()
    ├─ process()
    └─ _enhance_for_ocr()

OCREngine
├─ extract_text()
├─ extract_text_with_confidence()
├─ extract_structured_data()
└─ add_language()

DataExtractor
├─ extract_from_ocr_result()
├─ _extract_medicine_names()
├─ _extract_prescription_info()
├─ _extract_fields()
├─ format_for_cleaner()
└─ format_for_search()

Interfaces (ABC)
├── OCRPipeline (abstract)
│   ├─ process_pdf()
│   ├─ process_image()
│   ├─ register_data_cleaner()
│   └─ register_search_engine()
├── DataCleanerInterface (abstract)
│   ├─ clean()
│   └─ validate()
└── SearchEngineInterface (abstract)
    ├─ search()
    └─ search_by_medicine_name()

StandardOCRPipeline (implements OCRPipeline)
├─ process_pdf()
├─ process_image()
├─ process_and_clean()
├─ process_and_search()
├─ register_data_cleaner()
└─ register_search_engine()

MockDataCleaner (implements DataCleanerInterface)
├─ clean()
└─ validate()

MockSearchEngine (implements SearchEngineInterface)
├─ search()
└─ search_by_medicine_name()
```

## Module Dependencies

```
StandardOCRPipeline
├── PDFProcessor
├── ImageProcessor
├── OCREngine
│   └── pytesseract
│       └── tesseract-ocr (system)
├── DataExtractor
└── [External] DataCleanerInterface
└── [External] SearchEngineInterface

PDFProcessor
├── pdf2image
└── pillow (PIL)

ImageProcessor
├── pillow (PIL)
├── opencv-python (cv2)
└── numpy

OCREngine
├── pytesseract
└── pillow (PIL)

DataExtractor
└── re (Python stdlib)
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│             Your Cleaning/Validation Module                  │
│                                                              │
│  Implements: DataCleanerInterface                           │
│  Input:  ExtractedData                                      │
│  Output: Dict[str, Any] (your custom format)                │
│                                                              │
│  def clean(data: ExtractedData) -> Dict:                    │
│      # Your logic here                                       │
│                                                              │
│  def validate(data: Dict) -> bool:                          │
│      # Your validation here                                  │
└─────────────────────────────────────────────────────────────┘
              │
              │ pipeline.register_data_cleaner(your_cleaner)
              │
              ▼
        StandardOCRPipeline
        .process_and_clean()


┌─────────────────────────────────────────────────────────────┐
│            Your Search Engine Module                         │
│                                                              │
│  Implements: SearchEngineInterface                          │
│  Input:  medicine_name: str                                 │
│  Output: List[Dict] (drug records)                          │
│                                                              │
│  def search(query: str) -> List[Dict]:                      │
│      # Your search logic                                     │
│                                                              │
│  def search_by_medicine_name(name: str) -> List[Dict]:     │
│      # Your medicine name search logic                       │
└─────────────────────────────────────────────────────────────┘
              │
              │ pipeline.register_search_engine(your_engine)
              │
              ▼
        StandardOCRPipeline
        .process_and_search()
```

## Configuration Options

```
OCREngine
  languages: List[str]           # ['eng', 'fra', 'deu', ...]
  config: str                    # Tesseract PSM/OEM config

PDFProcessor
  dpi: int                       # 150, 300, 600

ImageProcessor
  enhance_quality: bool          # True (recommended), False
```

## Error Handling Flow

```
Pipeline.process_pdf/image()
  │
  ├─ Try: Processor.process()
  │  ├─ Validate file
  │  └─ Process document
  │  └─ Catch: Return error
  │
  ├─ Try: OCREngine.extract_text()
  │  └─ Catch: Return empty text
  │
  ├─ Try: DataExtractor.extract()
  │  └─ Catch: Return minimal data
  │
  └─ Try: External Module
     └─ Catch: Log warning, handle gracefully
```

---

This architecture ensures:
- **Separation of Concerns**: Each component has a single responsibility
- **Loose Coupling**: Components interact through well-defined interfaces
- **Easy Testing**: Mock modules provided
- **Extensibility**: Easy to add new languages, processors, extractors
- **Robustness**: Comprehensive error handling at each stage
