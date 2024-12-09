import json, re, os
import pymupdf
import langdetect
import jieba
import MeCab 
from typing import List

class pdfparser:
    PROGRESS_FILE = 'state/progress.json'
    TEXT_DIR = 'text/'
    TRANSLATED_DIR = 'translated/'
    def __init__(self, file_path, word_limit=50, min_words=10):
        self.setup_logging()
        self.file_path = file_path
        self.file_name = self._file_name_from_path(file_path)
        self.word_limit = word_limit
        self.min_words = min_words

        try:
            try:
                self.doc = pymupdf.open(file_path)
            except:
                self.doc = pymupdf.open(file_path, filetype="pdf")
        except:
            print("Error opening file")
            self.logger.error(f"Error opening file {self.file_name}")
            return
        #self.doc = pymupdf.open(file_path)

        if not os.path.exists(self.PROGRESS_FILE):
            os.makedirs("state", exist_ok=True)
            self.logger.info("Progress file not found. Creating a new one.")  
            with open(self.PROGRESS_FILE, "w") as f:
                json.dump([], f)
        if not os.path.exists(self.TEXT_DIR):
            os.makedirs(self.TEXT_DIR, exist_ok=True)
        if not os.path.exists(self.TRANSLATED_DIR):
            os.makedirs(self.TRANSLATED_DIR, exist_ok=True)
        self.TRANSLATED_FILE = os.path.join(self.TRANSLATED_DIR, self.file_name + ".txt")
        #create if not exists, append nothing if exists
        with open(self.TRANSLATED_FILE, "a+") as f:
            f.write("")

        self.state = self.load_progress(self.file_name)
        self.cursor = int(self.state["cursor"]) if self.state else 0
        self.language = self.state["language"] if self.state else self._detectlang(self.doc)
        self.text = self.convert()
        self.previous_chunk = self.state["previous_chunk"] if self.state else ""
        self.previous_translation = self.state["previous_translation"] if self.state else ""

    def get_metadata(self)->dict:
        """Get metadata of the document."""
        metadata = {
            "name": self.file_name,
            "language": self.language,
            "word_limit": self.word_limit,
            "length": len(self.doc)
        }
        return metadata
    def convert(self)->str:
        """Convert the PDF to text and store if not already done and return the text."""
        text = ""
        if os.path.exists(f"{self.TEXT_DIR}{self.file_name}.txt"):
            self.logger.info(f"Text file already exists for {self.file_name}. Skipping conversion.")
            with open(f"{self.TEXT_DIR}{self.file_name}.txt", "r") as f:
                text = f.read()
        
        else:
            self.logger.info(f"Converting {self.file_name} to text.")
            with open(f"{self.TEXT_DIR}{self.file_name}.txt", "w") as f:
                for page in self.doc:
                    f.write(page.get_text())
                    text += page.get_text()
        return text

    def parse(self)->str:
        """Returns a chunk of text from the document."""
        if self.cursor >= len(self.text):
            self.logger.info(f"Reached end of {self.file_name}.")  # Debugging log
            print(f"Reached end of {self.file_name}.")
            return None
        
        chunk = ""
        while len(self.split_text(chunk)) < self.word_limit and self.cursor < len(self.text):
            sentence_end = self._find_sentence_end(self.text[self.cursor:self.cursor + 1000])

            if sentence_end == len(self.text[self.cursor:]): 
                chunk += self.text[self.cursor:]
                self.cursor = len(self.text)
                break
            
            
            # Add the current sentence to the chunk
            chunk += self.text[self.cursor:self.cursor + sentence_end]
            self.cursor += sentence_end
        
        #Save progress
        self.save_progress({"file_name": self.file_name, "cursor": self.cursor, "language": self.language})
        
        return chunk
    
    def split_text(self, chunk)->List[str]:
        """Split the text into sentences."""
        if self.language == "ja":
            mecab = MeCab.Tagger("-Owakati")
            return mecab.parse(chunk).split()
        elif self.language == "zh":
            return list(jieba.cut(chunk))
        else:
            return chunk.split()

    def _find_sentence_end(self, text)->int:
        """
    Find the end of the sentence in the text.
    Returns the index of the end of the first complete sentence (relative to the text input).
    """
        if self.language == "ja":  
            mecab = MeCab.Tagger("-Owakati")
            words = mecab.parse(text).split()
            pattern = re.compile(
            r"[。！？](?![」』）】])"
        )
            offset = 0
            for word in words:
                if pattern.search(word):  
                    offset += len(word)+1 
                    return offset
                offset += len(word)  
            print("No match found")
            return len(text)  

        elif "zh" in self.language:  
            words = list(jieba.cut(text))
            pattern = re.compile(
                r"[。！？；](?![”』】])"  
        )
            offset = 0
            for word in words:
                if pattern.search(word):  
                    offset += len(word)  
                    return offset
                offset += len(word)  
            return len(text)  

        else:  
            pattern = re.compile(
                r"([.!?](?=\s|$)|\.\.\.(?=\s|$))"  
        )
            match = pattern.search(text)
            if match:
                return match.end()  
            return len(text)  


        


        
    def _detectlang(self, doc)->str:
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
            self.logger.warning("Language detection failed. Defaulting to English.")
            print("Language detection failed. Defaulting to English.")
            return "en"



    def load_progress(self, file_name)->dict:
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
        self.logger.info(f"No progress file found or no entry for {self.file_name}.")  # Debugging log
        return None

    
    def save_progress(self, state)->None:
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
        

        found = False
        for i in range(len(progress)):
            if progress[i]["file_name"] == self.file_name:
                #Update with only the fields provided
                progress[i].update(state)
                found = True
                break
                
        if not found:
            progress.append(state)

        if "previous_translation" in state:
            with open(self.TRANSLATED_FILE, "a+") as f:
                f.write(state["previous_translation"])

    # Write back to the file
        with open(self.PROGRESS_FILE, "w") as f:
            json.dump(progress, f)                
             
    def _file_name_from_path(self, file_path)->str:
        """Extract the file name from the file path."""
        if file_path.endswith('/'):
            file_path = file_path[:-1]
        #assert file_path.split('.')[-1] in {"pdf", "txt", "docx", "epub"}, "Unsupported file format"f

        return file_path.split('/')[-1]

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


#Test


if __name__=="__main__":
    pdf = pdfparser("static/uploads/1.pdf")
    while (input("Do you want to continue?")=="y"):
        print(pdf.parse())