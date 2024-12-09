let currentFile = null;
let currentPage = 0;
let currentCursor = 0;
let previousChunk = null;
let previousTranslation = null;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('nextButton').addEventListener('click', getNextChunk);
    document.getElementById('acceptButton').addEventListener('click', acceptTranslation);
    document.getElementById('redoButton').addEventListener('click', redoTranslation);
    
    if (window.metadata && window.metadata.file_name) {
        currentFile = window.metadata.file_name;
    }
});

async function displayMetadata(metadata) {
    try {
        const metadataText = `
            <strong>Name:</strong> ${metadata.name.replace('uploads', '')}<br>
            <strong>Language:</strong> ${metadata.language}<br>
            <strong>Chunk Word Limit:</strong> ${metadata.word_limit}<br>
            <strong>Length:</strong> ${metadata.length} pages
        `;
        document.getElementById('metadataText').innerHTML = metadataText;
    } catch (error) {
        console.error('Error displaying metadata:', error);
    }
}


async function getNextChunk() {
    try {
        if (!currentFile) {
            alert('No file selected');
            return;
        }
        const response = await fetch('/get_chunk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: currentFile,
            })
        });
        const data = await response.json();
        console.log('Response:', data);
        if (data.success) {
            // Store the current chunk before updating
            previousChunk = document.getElementById('currentText').textContent;
            previousTranslation = document.getElementById('translatedText').value;

            document.getElementById('currentText').textContent = data.text;
            currentCursor = data.cursor;

            // Pass previous chunk and translation
            translateChunk(data.text, previousChunk, previousTranslation);
            console.log(previousChunk);
            //console.log(previousTranslation);
        } else if (data.error === 'End of document') {
            // Handle end of document
            console.log('End of document');
        }
    } catch (error) {
        console.error('Error fetching chunk:', error);
    }
}

async function translateChunk(text, previousChunk, previousTranslation) {
    try {
        console.log("Inside translateChunk");
        console.log(JSON.stringify({
            text: text,
            previous_chunk: previousChunk,
            previous_translation: previousTranslation,
            filename: currentFile // Pass the filename for progress tracking
        })
        )
        const response = await fetch('/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                text: text,
                previous_chunk: previousChunk,
                previous_translation: previousTranslation,
                filename: currentFile // Pass the filename for progress tracking
            })
        });

        const data = await response.json();
        
        if (data.success) {
            const translatedText = Array.isArray(data.translation.translated_text) 
                ? data.translation.translated_text[0] 
                : data.translation.translated_text;
            document.getElementById('translatedText').value = translatedText;
            
            // Update word list with extracted terms
            updateWordList(data.translation.extracted_terms);
            
            // Update the previous chunk and translation for next time
            previousChunk = text;
            previousTranslation = data.translation.translated_text;
        }
    } catch (error) {
        console.error('Error translating text:', error);
    }
}



// Function to update the word list display
function updateWordList(terms) {
    const wordList = document.getElementById('wordList');
    terms.forEach(term => {
        const entry = document.createElement('div');
        entry.className = 'word-entry';
        entry.innerHTML = `
            <span><strong>${term.term}:</strong> ${term.suggested_translation}</span>
            <button class="delete-btn" onclick="deleteEntry(this)">Delete</button>
            <div class="cultural-note">${term.cultural_significance}</div>
        `;
        wordList.appendChild(entry);
    });
}

// Function to delete a word-translation entry
function deleteEntry(button) {
    button.parentElement.remove();
}

// Add event listener for adding new translations
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('addTranslation').addEventListener('click', () => {
        const word = document.getElementById('wordInput').value;
        const translation = document.getElementById('translationInput').value;
        
        if (word && translation) {
            const wordList = document.getElementById('wordList');
            const entry = document.createElement('div');
            entry.className = 'word-entry';
            entry.innerHTML = `
                <span><strong>${word}:</strong> ${translation}</span>
                <button class="delete-btn" onclick="deleteEntry(this)">Delete</button>
            `;
            wordList.appendChild(entry);
            
            // Clear inputs
            document.getElementById('wordInput').value = '';
            document.getElementById('translationInput').value = '';
        }
    });
});

// Accept current translation
async function acceptTranslation() {
    try {
        const translatedText = document.getElementById('translatedText').value;
        const currentText = document.getElementById('currentText').textContent;
        const storedText = document.getElementById('storedText');
        
        // Add current translation to stored text
        storedText.value += translatedText + '\n\n';
        
        // Save progress to server
        await fetch('/save_progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: currentFile,
                original: currentText,
                translation: translatedText,
                cursor: currentCursor
            })
        });
        
        // Get next chunk
        getNextChunk();
    } catch (error) {
        console.error('Error saving translation:', error);
    }
}

// Redo translation
function redoTranslation() {
    const currentText = document.getElementById('currentText').textContent;
    if (currentText) {
        translateChunk(currentText, previousChunk, previousTranslation);
    }
}


