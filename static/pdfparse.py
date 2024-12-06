import json, re, os
import pymupdf
import langdetect
import jieba
import MeCab 

class pdfparser:
    PROGRESS_FILE = 'state/progress.json'
    TEXT_DIR = 'text/'
    def __init__(self, file_path, word_limit=75, min_words=10):
        self.setup_logging()
        self.file_path = file_path
        self.file_name = self._file_name_from_path(file_path)
        self.word_limit = word_limit
        self.min_words = min_words

        try:
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

        self.state = self.load_progress(self.file_name)
        self.cursor = self.state["cursor"] if self.state else 0
        self.language = self.state["language"] if self.state else self._detectlang(self.doc)
        self.text = self.convert()


    def convert(self):
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

    def parse(self):
        """Returns a chunk of text from the document."""
        if self.cursor >= len(self.text):
            self.logger(f"Reached end of document.")
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
    
    def split_text(self, chunk):
        """Split the text into sentences."""
        if self.language == "ja":
            mecab = MeCab.Tagger("-Owakati")
            return mecab.parse(chunk).split()
        elif self.language == "zh":
            return list(jieba.cut(chunk))
        else:
            return chunk.split()

    def _find_sentence_end(self, text):
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
            self.logger.warning("Language detection failed. Defaulting to English.")
            print("Language detection failed. Defaulting to English.")
            return "en"



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
        self.logger.info(f"No progress file found or no entry for {self.file_name}.")  # Debugging log
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
        for i in range(len(progress)):
            if progress[i]["file_name"] == self.file_name:
                progress[i] = state
                break
        else:
            progress.append(state)

    # Write back to the file
        with open(self.PROGRESS_FILE, "w") as f:
            json.dump(progress, f)                
             
    def _file_name_from_path(self, file_path):
        """Extract the file name from the file path."""
        if file_path.endswith('/'):
            file_path = file_path[:-1]
        #assert file_path.split('.')[-1] in {"pdf", "txt", "docx", "epub"}, "Unsupported file format"
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

#pdf = pdfparser("static/1.pdf")

while (input("Do you want to continue?")=="y"):
    print(pdf.parse())