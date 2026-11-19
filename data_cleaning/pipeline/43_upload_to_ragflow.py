"""
43_upload_to_ragflow.py
===========================
Uploads all drug notice text files from the drug_notices folder to RAGFlow via the ragflow_sdk.
Creates a separate dataset for each language.
"""

import os
from pathlib import Path
import time

try:
    from ragflow_sdk import RAGFlow
except ImportError:
    print("Error: The 'ragflow_sdk' is not installed.")
    print("Please install it using: pip install ragflow-sdk")
    exit(1)

# ────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning\drug_notices")
LANGUAGES = ["arabic", "english", "french"]

# RAGFlow API Configuration
# Replace these with your actual RAGFlow API key and server URL
API_KEY = os.environ.get("RAGFLOW_API_KEY", "ragflow-NQZlEdTyUs1Qj4CYRTb8ZiEoibPuFaYl6C8V0cofIbI")
BASE_URL = os.environ.get("RAGFLOW_BASE_URL", "https://rag.medicamentdz.com/")
DATASET_NAME_PREFIX = "Drug_Notices"

BATCH_SIZE = 50  # Upload in batches to avoid timing out

# ────────────────────────────────────────────────────────────────────
# Main Upload Logic
# ────────────────────────────────────────────────────────────────────
def main():
    if not API_KEY or API_KEY == "ragflow-NQZlEdTyUs1Qj4CYRTb8ZiEoibPuFaYl6C8V0cofIbI":
        print("Please edit this script to insert your valid RAGFlow API Key and Base URL.")
        return

    print("Initializing RAGFlow Client...")
    rag = RAGFlow(api_key=API_KEY, base_url=BASE_URL)
    
    total_successful_uploads = 0
    total_files_found = 0

    for lang in LANGUAGES:
        lang_dir = BASE_DIR / lang
        if not lang_dir.exists():
            continue
            
        files = list(lang_dir.glob("*.txt"))
        if not files:
            continue
            
        total_files_found += len(files)
        dataset_name = f"{DATASET_NAME_PREFIX}_{lang.capitalize()}"
        
        print("\n" + "-" * 50)
        print(f"Processing Language: {lang.capitalize()}")
        print("-" * 50)
        print(f"Retrieving or creating dataset: '{dataset_name}'...")
        
        datasets = rag.list_datasets(name=dataset_name)
        if datasets:
            dataset = datasets[0]
            print(f"Found existing dataset with ID: {dataset.id}")
        else:
            dataset = rag.create_dataset(name=dataset_name)
            print(f"Created new dataset with ID: {dataset.id}")
            
        print(f"Total files to upload for {lang}: {len(files)}\n")
        
        lang_successful = 0
        
        for i in range(0, len(files), BATCH_SIZE):
            batch_files = files[i:i + BATCH_SIZE]
            documents_payload = []
            
            for file_path in batch_files:
                try:
                    with open(file_path, "rb") as f:
                        blob = f.read()
                    
                    # We can just use the filename since they are separated by language datasets now
                    display_name = file_path.name
                    
                    documents_payload.append({
                        "display_name": display_name,
                        "blob": blob
                    })
                except Exception as e:
                    print(f"Error reading file {file_path.name}: {e}")

            if not documents_payload:
                continue

            print(f"Uploading batch {i//BATCH_SIZE + 1} (files {i+1} to {min(i+BATCH_SIZE, len(files))})...")
            
            try:
                # Upload the documents to the dataset
                dataset.upload_documents(documents_payload)
                lang_successful += len(documents_payload)
                
                # Optional: To avoid hitting API rate limits
                time.sleep(1)
            except Exception as e:
                print(f"Failed to upload batch starting at index {i}. Error: {e}")
                
        total_successful_uploads += lang_successful
        print(f"Finished {lang.capitalize()}: {lang_successful} files uploaded.")

    print("\n" + "="*50)
    print("UPLOAD COMPLETE")
    print(f"Successfully uploaded: {total_successful_uploads} / {total_files_found} files across all languages")
    print("="*50)
    print("\nNote: The files have been uploaded to their respective datasets, but may still need to be parsed/indexed.")
    print("You can trigger the parsing process from the RAGFlow UI or via the dataset.async_parse_documents() method.")

if __name__ == "__main__":
    main()
