import os
import random
import string
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for

# Flask app configuration
app = Flask(__name__)

# Folders for uploads and pastes
UPLOAD_FOLDER = 'uploads'
PASTEBIN_FOLDER = 'pastes'

# Ensure the folders for uploads and pastes exist
for folder in [UPLOAD_FOLDER, PASTEBIN_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Function to generate a random 6-character string
def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Main index route
@app.route('/')
def index():
    return render_template('index.html')

# File upload route
@app.route('/api/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    file_urls = []
    for file in files:
        if file:
            # Generate a 6-character alphanumeric string for the file ID
            short_id = generate_short_id()

            # Get the file extension
            file_extension = os.path.splitext(file.filename)[1]

            # Save the file using the short ID and the original extension
            file_id = f"{short_id}{file_extension}"
            file.save(os.path.join(UPLOAD_FOLDER, file_id))
            
            # Generate the file URL
            file_url = url_for('get_file', file_id=file_id, _external=True)
            file_urls.append(file_url)

    return jsonify({'urls': file_urls}), 201

# Serve uploaded files
@app.route('/files/<file_id>', methods=['GET'])
def get_file(file_id):
    try:
        return send_from_directory(UPLOAD_FOLDER, file_id)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

# Paste creation route
@app.route('/api/paste', methods=['POST'])
def create_paste():
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Content cannot be empty'}), 400

    unique_id = str(uuid.uuid4())
    paste_file = f"{unique_id[:6]}.txt"  # Shorten the UUID for pastes too, if desired
    with open(os.path.join(PASTEBIN_FOLDER, paste_file), 'w') as f:
        f.write(content)

    paste_url = url_for('view_paste', paste_id=unique_id[:6], _external=True)
    return jsonify({'url': paste_url}), 201

# Serve and view pastes
@app.route('/pastes/<paste_id>', methods=['GET'])
def view_paste(paste_id):
    try:
        with open(os.path.join(PASTEBIN_FOLDER, f"{paste_id}.txt"), 'r') as f:
            content = f.read()
        return render_template('view_paste.html', content=content, paste_id=paste_id)
    except FileNotFoundError:
        return jsonify({'error': 'Paste not found'}), 404
    
@app.route('/pastes/raw/<paste_id>', methods=['GET'])
def view_paste_raw(paste_id):
    try:
        with open(os.path.join(PASTEBIN_FOLDER, f"{paste_id}.txt"), 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain'}
    except FileNotFoundError:
        return jsonify({'error': 'Paste not found'}), 404

# Error handling for 404 routes
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Page not found'}), 404

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
