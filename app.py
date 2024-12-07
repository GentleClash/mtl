from flask import Flask, request, jsonify, render_template, url_for, redirect
from static.pdfparse import pdfparser
from static.translate import initialize_model, translate_text, process_glossaries
from static.prompts import UserPrompt, TranslationOutput
from typing import List
import pymupdf, re, json, os, time, base64, jieba, MeCab, langdetect
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATE_FOLDER'] = 'state'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# Initialize translation model
model, input_template = initialize_model()
glossaries = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file provided')
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            print('No file selected')
            return jsonify({'success': False, 'error': 'No file selected'})
        
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f'File saved to {filepath}')

        return redirect(url_for('manual_edit', filename=filename))
        
        #return jsonify({'success': True, 'filename': filename})
    
    return render_template('index.html')
@app.route('/get_chunk', methods=['POST'])
def get_chunk():
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'error': 'No filename provided'})
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'File not found'})

    try:
        parser = pdfparser(filepath)
        chunk = parser.parse()
        
        if chunk is None:
            return jsonify({'success': False, 'error': 'End of document'})
        
        # Save progress for the file, including the current chunk
        parser.save_progress({
            "file_name": filename,
            "cursor": parser.cursor,
            "previous_chunk": chunk
        })

        return jsonify({
            'success': True,
            'text': chunk,
            'cursor': parser.cursor,
            'language': parser.language
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '')
    filename = data.get('filename')
    
    if not text or not filename:
        return jsonify({'success': False, 'error': 'No text or filename provided'})

    # Retrieve previous chunk and translation
    previous_chunk, previous_translation = None, None
    progress_file = os.path.join(app.config['STATE_FOLDER'], 'progress.json')
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
                for entry in progress:
                    if entry.get('file_name') == filename:
                        previous_chunk = entry.get('last_chunk')
                        previous_translation = entry.get('last_translation')
                        break
        except json.JSONDecodeError:
            pass  

    try:
        translation = translate_text(text, glossaries, model, input_template, previous_chunk, previous_translation)

        # Save the latest translation for progress tracking
        parser = pdfparser(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        parser.save_progress({
            "file_name": filename,
            "cursor": parser.cursor,
            "previous_chunk": text,
            "previous_translation": translation
        })

        return jsonify({'success': True, 'translation': translation})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/manual_edit/<filename>')
def manual_edit(filename):
    progress_file = os.path.join(app.config['STATE_FOLDER'], 'progress.json')
    os.makedirs(app.config['STATE_FOLDER'], exist_ok=True)  
    
    def initialize_progress(file_name):
        """Helper function to initialize progress."""
        try:
            parser = pdfparser(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
            parser.save_progress({
                "file_name": file_name,
                "cursor": 0,
                "previous_chunk": "",
                "previous_translation": "",
                "language": parser.language
            })
            return parser.language
        except Exception as e:
            return None

    # Check if progress.json exists, if not, initialize it
    if not os.path.exists(progress_file):
        language = initialize_progress(filename)
        if "zh" in language:
            language = "zh"
        if language is None:
            return jsonify({'error': 'Failed to initialize progress'}), 400

    try:
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress = json.load(f)
                
                # Check if the filename is already tracked in progress
                for entry in progress:
                    if entry.get('file_name') == filename:
                        return render_template(
                            'edit_index.html', 
                            file_name=filename,
                            cursor=entry.get('cursor', 0),
                            previous_chunk=entry.get('previous_chunk', ""),
                            previous_translation=entry.get('previous_translation', ""),
                            language=entry.get('language', "")
                        )

                # If filename not found, initialize it
                language = initialize_progress(filename)
                if language is None:
                    return jsonify({'error': 'Failed to initialize progress'}), 400

        # Try one more time after initialization
        with open(progress_file, 'r') as f:
            progress = json.load(f)
            for entry in progress:
                if entry.get('file_name') == filename:
                    return render_template(
                        'edit_index.html', 
                        filename=filename,
                        cursor=entry.get('cursor', 0),
                        last_chunk=entry.get('previous_chunk', ""),
                        last_translation=entry.get('previous_translation', ""),
                        language=entry.get('language', "")
                    )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Failed to process file progress'}), 500

@app.route('/metadata')
def get_metadata_():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'success': False, 'error': 'No filename provided'})

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'File not found'})

    try:
        parser = pdfparser(filepath)
        metadata = parser.get_metadata()
        return jsonify({'success': True, 'metadata': metadata})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



@app.route('/save_progress', methods=['POST', 'GET'])
def save_progress():
    data = request.json
    
    filename = data.get('file_name')
    if not filename:
        return jsonify({'success': False, 'error': 'Filename missing'}), 400

    progress_file = os.path.join(app.config['STATE_FOLDER'], 'progress.json')
    try:
        with open(progress_file, 'r+') as f:
            progress = json.load(f)
            for entry in progress:
                if entry['file_name'] == filename:
                    entry.update(data) 
            f.seek(0)
            json.dump(progress, f, indent=4)
            f.truncate()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    return redirect(url_for('translate_interface', filename=filename))


@app.route('/translate_interface/', methods=['GET'])
def translate_interface():
    file_name = request.args.get('file_name')
    
    if not file_name:
        print("No file name provided. Redirecting to home.")
        return redirect(url_for('home'))
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    if not os.path.exists(filepath):
        print(f"File {file_name} not found in upload folder. Redirecting to home.")
        return redirect(url_for('home'))
    
    try:
        metadata = pdfparser(filepath).get_metadata()
        print(f"Metadata: {metadata}")
        return render_template('translate.html', metadata=metadata)
    except Exception as e:
        print(f"Error getting metadata: {str(e)}")
        return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)