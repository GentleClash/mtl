import fitz  
import json
import os


PROGRESS_FILE = "static/pdf_progress.json"
WORD_LIMIT = 100




def save_progress(file_path, page_number, cursor):
    """Save the current progress to a JSON file."""
    progress = []
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                progress = json.load(f)
        except json.JSONDecodeError:
            progress = []
    for i in range(len(progress)):
        if progress[i]["file_path"].split("/")[-1] == file_path.split("/")[-1]:
            progress[i]["page_number"] = page_number
            progress[i]["cursor"] = cursor
            with open(PROGRESS_FILE, "w") as f:
                json.dump(progress, f)
            return

    progress.append({
        "file_path": file_path,
        "page_number": page_number,
        "cursor": cursor
    })
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)



def load_progress(file_path):
    """Load progress from the JSON file if it exists."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                for i in json.load(f):
                    if i["file_path"].split('/')[-1] == file_path.split('/')[-1]:
                        return i
        except json.JSONDecodeError:
            return None
    return None

def parse_pdf(file_path):
    """Parse the PDF incrementally."""
    doc = fitz.open(file_path)

    progress = load_progress(file_path)
    page_number = 0
    cursor = 0

    if progress and progress["file_path"].split('/')[-1] == file_path.split('/')[-1]:
        page_number = progress["page_number"]
        cursor = progress["cursor"]
        print(f"Resuming from page {page_number + 1}, cursor position {cursor}")

    while page_number < len(doc):
        page = doc[page_number]
        text = page.get_text("text")  
        lines = text.splitlines()
        
        word_count = 0
        current_chunk = []

        i = cursor
        while i < len(lines):
            current_line = lines[i]
            words_in_line = current_line.split()
            
            if word_count + len(words_in_line) <= WORD_LIMIT:
                current_chunk.append(current_line)
                word_count += len(words_in_line)
                i += 1
            else:
                if word_count == 0:  
                    current_chunk.append(current_line)
                    i += 1
                break
                
            if i >= len(lines):  
                break

        if current_chunk:
            print(f"Page {page_number + 1}, Chunk starting at line {cursor + 1}:")
            print('\n'.join(current_chunk))

            user_input = input("Continue parsing? (y/n/save): ").strip().lower()
            if user_input == "n":
                print("Stopping...")
                return
            elif user_input == "save":
                print("Progress saved.")
                save_progress(file_path, page_number, i)
                return

        page_number += 1
        cursor = 0  

    print("Reached the end of the document.")
    save_progress(file_path, page_number, 0)

if __name__ == "__main__":
    pdf_path = input("Enter the path to the PDF file: ").strip()
    if os.path.exists(pdf_path):
        parse_pdf(pdf_path)
    else:
        print("File not found!")
