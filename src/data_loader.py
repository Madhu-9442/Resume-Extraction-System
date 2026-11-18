from pathlib import Path

def load_data(file_path):

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if file_path.suffix.lower() != '.txt':
        raise ValueError("only .txt files are supported")

    text = file_path.read_text(encoding='utf-8')

    if not text.strip():
        raise ValueError(f'Resume file is empty: {file_path}')

    return text


text = load_data(r"C:\Users\DELL\OneDrive\Desktop\GenAI_WDB_28th_Sep\resumes\resume_extraction\data\resumes\CAND001.txt")
print(text)