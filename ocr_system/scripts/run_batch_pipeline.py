#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

# Setup paths to ensure our module imports work regardless of where the script is called from
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.pipeline import MedicalOCRPipeline

def main():
    parser = argparse.ArgumentParser(description="Batch process medical documents through OCR and Parsing")
    parser.add_argument("--input", "-i", type=str, default="data/sample_images", 
                        help="Input directory or file (default: data/sample_images)")
    parser.add_argument("--output", "-o", type=str, default="data/output_texts", 
                        help="Output directory for raw txt and parsed json (default: data/output_texts)")
    
    args = parser.parse_args()
    
    # Resolve absolute paths
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = project_root / input_path
        
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path
        
    if not input_path.exists():
        print(f"Error: Input path '{input_path}' does not exist.")
        sys.exit(1)

    print("="*50)
    print("🚀 INITIALIZING MEDICAL OCR BATCH PIPELINE 🚀")
    print("="*50)
    
    pipeline = MedicalOCRPipeline()
    
    if input_path.is_file():
        print(f"Processing SINGLE file: {input_path.name}\n")
        pipeline.process_file(input_path, output_path)
    else:
        print(f"Processing BATCH directory: {input_path.name}\n")
        pipeline.process_directory(input_path, output_path)
        
    print("\n" + "="*50)
    print("✅ PIPELINE EXECUTION COMPLETE ✅")
    print(f"Results saved to: {output_path}")
    print("="*50)

if __name__ == "__main__":
    main()
