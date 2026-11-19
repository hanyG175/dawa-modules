import os
from pathlib import Path

# Maximum target size per split file in bytes (e.g., 5 MB)
MAX_FILE_SIZE = 5 * 1024 * 1024
SEPARATOR = "\n\n" + "="*80 + "\n\n"

def split_txt_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    chunks = content.split(SEPARATOR)
    chunks = [c for c in chunks if c.strip()]
    
    file_idx = 1
    current_size = 0
    current_chunks = []
    
    base_name = file_path.stem
    dir_path = file_path.parent
    
    for chunk in chunks:
        chunk_text = chunk + SEPARATOR
        chunk_size = len(chunk_text.encode('utf-8'))
        
        if current_size + chunk_size > MAX_FILE_SIZE and current_chunks:
            out_name = dir_path / f"{base_name}_part{file_idx:02d}.txt"
            with open(out_name, 'w', encoding='utf-8') as f_out:
                f_out.write("".join(current_chunks))
            file_idx += 1
            current_chunks = [chunk_text]
            current_size = chunk_size
        else:
            current_chunks.append(chunk_text)
            current_size += chunk_size
            
    if current_chunks:
        out_name = dir_path / f"{base_name}_part{file_idx:02d}.txt"
        with open(out_name, 'w', encoding='utf-8') as f_out:
            f_out.write("".join(current_chunks))
            
    file_path.unlink()

def split_jsonl_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    file_idx = 1
    current_size = 0
    current_lines = []
    
    base_name = file_path.stem
    dir_path = file_path.parent
    
    for line in lines:
        line_size = len(line.encode('utf-8'))
        
        if current_size + line_size > MAX_FILE_SIZE and current_lines:
            out_name = dir_path / f"{base_name}_part{file_idx:02d}.jsonl"
            with open(out_name, 'w', encoding='utf-8') as f_out:
                f_out.writelines(current_lines)
            file_idx += 1
            current_lines = [line]
            current_size = line_size
        else:
            current_lines.append(line)
            current_size += line_size
            
    if current_lines:
        out_name = dir_path / f"{base_name}_part{file_idx:02d}.jsonl"
        with open(out_name, 'w', encoding='utf-8') as f_out:
            f_out.writelines(current_lines)
            
    file_path.unlink()

def main():
    rag_dir = Path("new_data_rag")
    for ext in ['*.txt', '*.jsonl']:
        for file_path in rag_dir.rglob(ext):
            if '_part' not in file_path.name:
                print(f"Splitting {file_path}...")
                if ext == '*.txt':
                    split_txt_file(file_path)
                else:
                    split_jsonl_file(file_path)
    print("Splitting complete.")

if __name__ == '__main__':
    main()
