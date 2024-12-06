import json, re, os
import pymupdf
import langdetect
import jieba
import MeCab  
from collections import deque

class pdfparser:
    PROGRESS_FILE = "state/pdf_progress.json"
    def __init__(self, file_path, word_limit=500, min_words=100):
        self.setup_logging()
        self.file_path = file_path
        self.file_name = self._file_name_from_path(file_path)
        self.doc = pymupdf.open(file_path)
        if not os.path.exists(self.PROGRESS_FILE):
            os.makedirs("state", exist_ok=True)
            self.logger.info("Progress file not found. Creating a new one.")  
            with open(self.PROGRESS_FILE, "w") as f:
                json.dump([], f)

        self.state = self.load_progress(self.file_name)
        self.word_limit = word_limit
        self.min_words = min_words

        self.page_number = self.state["page_number"] if self.state else 0
        self.cursor = self.state["cursor"] if self.state else 0
        self.language = self.state["language"] if self.state else self._detectlang(self.doc)
        self.logger.info(f"Loaded progress for {self.file_name} at page {self.page_number} cursor {self.cursor} language {self.language}")

    def parse_document(self):
        chunks = deque()
        page_count = len(self.doc)
        pages_parsed = 0
        parse_cursor = self.cursor

        #Skip empty pages
        while not self.doc[self.page_number].get_text():
            self.page_number+=1


        while self.page_number < page_count and pages_parsed < 2:
            try:
                current_page = self.doc[self.page_number]
                next_page = self.doc[self.page_number + 1] if self.page_number + 1 < page_count else None
            except IndexError:
                current_page = self.doc[self.page_number]
                next_page = None
            current_page_content = current_page.get_text()
            next_page_content = next_page.get_text() if next_page else ""

            current_chunks = self._parse_page(current_page_content, next_page_content, parse_cursor)
            chunks.extend(current_chunks)
            
            if not current_page_content[parse_cursor:].strip() or current_chunks:
                self.page_number += 1
                parse_cursor = 0
                pages_parsed += 1

        return chunks



    def _parse_page(self, current_page_text, next_page_text, cursor):
        if not current_page_text.strip():
            return []

        current_chunks = []
        current_page_text = current_page_text[cursor:]

        while current_page_text:
        # Find the end of the first sentence
            new_cursor = self._find_sentence_end(current_page_text)

        # Check if the sentence spans into the next page
            if new_cursor == len(current_page_text) and next_page_text:
                next_page_sentence_end = self._find_sentence_end(next_page_text)
                current_page_text += next_page_text[:next_page_sentence_end]
                new_cursor += next_page_sentence_end

            # Update the next page and cursor
                self.page_number += 1
                cursor = next_page_sentence_end

            # Remove the used part of the next page text
                next_page_text = next_page_text[next_page_sentence_end:]
            else:
                cursor+=new_cursor

        # Slice the chunk and append it
            chunk = current_page_text[:new_cursor]
            current_chunks.append(chunk)

        # Update remaining text on the current page
            current_page_text = current_page_text[new_cursor:]

        # Handle minimum word limits, combining chunks if necessary
            """if len(chunk.split()) < self.min_words and current_page_text:

                next_new_cursor = self._find_sentence_end(current_page_text)
                chunk += current_page_text[:next_new_cursor]
                current_chunks[-1] = chunk
                current_page_text = current_page_text[next_new_cursor:]
                cursor += next_new_cursor"""

        return current_chunks

    def consume_chunk(self, chunks):
        """Consume a chunk from the deque and return it."""
        if not chunks:
            return None
        chunk = chunks.popleft()

        self.cursor += len(chunk)

        self.save_progress({
            "file_name": self.file_name,
            "page_number": self.page_number,
            "cursor": self.cursor,
            "language": self.language
        })

        return chunk


    def _find_sentence_end(self, text):
        # Tokenize based on language
        if self.language == "en":
            return self._find_sentence_end_en(text)
        elif self.language == "ja":
            return self._find_sentence_end_ja(text)
        elif "zh" in self.language:
            return self._find_sentence_end_zh(text)
        else:
            # Default fallback: Assume space-delimited languages
            tokens = text.split()
            sentence_end_pattern = re.compile(r'[.!?]')
            for i, word in enumerate(tokens):
                if sentence_end_pattern.search(word):
                    return len(" ".join(tokens[:i + 1]))
            return len(text)
        
    def _find_sentence_end_en(self, text):
        """
        Finds the end of the first sentence in English text using regular expressions.
        Returns the index where the sentence ends.
        """
        # Pattern to match sentence-ending punctuation followed by a space or the end of the string
        sentence_end_pattern = re.compile(r'[.!?](?=\s|$)')
        match = sentence_end_pattern.search(text)

        if match:
            # Return the index after the matched sentence-ending character
            return match.end()
        else:
            # No complete sentence found, return the length of the text
            return len(text)

    def _find_sentence_end_ja(self, text):
        """
        Finds the end of the first sentence in Japanese text.
        Uses MeCab to tokenize and heuristically determine sentence boundaries.
        """
        mecab = MeCab.Tagger("-Owakati")  # Word tokenizer mode
        tokens = mecab.parse(text).split()
        sentence_end_indices = []

        # Japanese sentence-ending particles are like "。", "！", "？"
        for i, token in enumerate(tokens):
            if token in {"。", "？"}:
                sentence_end_indices.append(i)

        if sentence_end_indices:
            # Find the position of the sentence-ending token
            end_index = sentence_end_indices[-1]
            try:
                end_index = sentence_end_indices[2]
            except:
                try:
                    end_index = sentence_end_indices[1]
                except:
                    end_index = sentence_end_indices[0]
            
            # Return the corresponding character index
            return len("".join(tokens[:end_index]))+1
            
        else:
            # No complete sentence found
            return len(text)

    def _find_sentence_end_zh(self, text):
        """
        Finds the end of the first sentence in Chinese text.
        Uses Jieba for tokenization and heuristically determines sentence boundaries.
        """
        tokens = list(jieba.cut(text))
        sentence_end_indices = []

        # Chinese sentence-ending characters are like "。", "！", "？"
        for i, token in enumerate(tokens):
            if token in {"。", "！", "？"}:
                sentence_end_indices.append(i)

        if sentence_end_indices:
            # Find the position of the first sentence-ending token
            try:
                end_index = sentence_end_indices[2]
            except:
                try:
                    end_index = sentence_end_indices[1]
                except:
                    end_index = sentence_end_indices[0]
            # Return the corresponding character index
            return len("".join(tokens[:end_index + 1]))
        else:
            # No complete sentence found
            return len(text)

                

    def setup_logging(self):
        """
        Configure logging for tracking parsing process
        """
        import logging
        logging.basicConfig(
            filename='document_parsing.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _file_name_from_path(self, file_path):
        """Extract the file name from the file path."""
        if file_path.endswith('/'):
            file_path = file_path[:-1]
        assert file_path.split('.')[-1] in {"pdf", "txt", "docx", "epub"}, "Unsupported file format"
        return file_path.split('/')[-1]

    def load_progress(self, file_name):
        """Load progress from the JSON file if it exists."""
        if os.path.exists(self.PROGRESS_FILE):
            try:
                with open(self.PROGRESS_FILE, "r") as f:
                    for i in json.load(f):
                        if i["file_name"] == file_name:
                            self.logger.info("Progress loaded successfully.")  # Debugging log
                            return i
            except json.JSONDecodeError:
                self.logger.warning(f"{self.PROGRESS_FILE} is corrupted. Ignoring.")
                return None
        self.logger.info("No progress file found or no entry for this file.")  # Debugging log
        return None

    
    def save_progress(self, state):
        """Save the current progress to a JSON file."""
        progress = []
        if os.path.exists(self.PROGRESS_FILE):
            #self.logger.info(f"{self.PROGRESS_FILE} exists. Loading progress.")  # Debugging log
            try:
                with open(self.PROGRESS_FILE, "r") as f:
                    progress = json.load(f)
            except json.JSONDecodeError:
                self.logger.warning(f"{self.PROGRESS_FILE} is corrupted. Overwriting.")
                progress = []

    # Update or append the current file's progress
        for i in range(len(progress)):
            if progress[i]["file_name"] == self.file_name:
                progress[i] = state
                break
        else:
            progress.append(state)

    # Write back to the file
        with open(self.PROGRESS_FILE, "w") as f:
            json.dump(progress, f)

    
    def _detectlang(self, doc):
        """Detect the language of the text."""
        #Skip empty pages
        page=0
        while not doc[page].get_text():
            page+=1
        try:
            lang = langdetect.detect(doc[page].get_text()[:100])
            if lang =="ja":
                return "ja"
            elif "zh" in lang:
                return "zh"
            else:
                return "en"
        except langdetect.lang_detect_exception.LangDetectException:
            return "en"

#Test
#jp
#pdf = pdfparser(r"/home/ayush/Downloads/Telegram Desktop/震電_みひろ_彼女が先輩にNTRれたので、先輩の彼女をNTRます３.epub")

#en
pdf = pdfparser(r"/home/ayush/Downloads/Telegram Desktop/Death Another Note.pdf")

#zh
#pdf = pdfparser(r"/home/ayush/Documents/CN.pdf")

input("Press any key to continue")
import time
time.sleep(2)

chunks = pdf.parse_document()

while chunks:
    print("Next chunk is ready.")
    user_input = input("Do you want to continue? (y/n): ").strip().lower()

    if user_input == "y":
        # Consume and display the next chunk
        chunk = pdf.consume_chunk(chunks)
        print("Consumed chunk:", chunk)
    else:
        # User stops processing
        print("Stopping processing.")
        break

