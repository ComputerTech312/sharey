from flask import Blueprint, request, jsonify, url_for, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename
import hashlib

# Create a Blueprint for the API
api_bp = Blueprint('api', __name__)

# Configurations (use these from the app's config when importing)
UPLOAD_FOLDER = 'uploads'
PASTEBIN_FOLDER = 'pastes'

# Helper function to check for allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg', 'webp',
        'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', '3gp',
        'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'rtf',
        'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma',
        'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz',
        'py', 'js', 'html', 'css', 'php', 'java', 'c', 'cpp', 'h', 'hpp', 'xml', 'json', 'yaml', 'csv'
    }

# Helper function to compute the SHA-256 hash of a file
def file_hash(file):
    hasher = hashlib.sha256()
    for chunk in iter(lambda: file.read(4096), b""):
        hasher.update(chunk)
    file.seek(0)  # Reset file pointer to the beginning after reading
    return hasher.hexdigest()

# API: File Upload with Duplicate Detection
@api_bp.route('/upload', methods=['POST'])
def api_upload_file():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files part in the request'}), 400

    files = request.files.getlist('files[]')
    file_urls = []

    for file in files:
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            # Compute the hash of the file to detect duplicates
            hash_value = file_hash(file)

            # Check if a file with the same hash already exists
            existing_file = None
            for existing_filename in os.listdir(UPLOAD_FOLDER):
                existing_file_path = os.path.join(UPLOAD_FOLDER, existing_filename)
                with open(existing_file_path, 'rb') as f:
                    if file_hash(f) == hash_value:
                        existing_file = existing_filename
                        break

            if existing_file:
                # File with the same content exists, return the existing file URL
                file_url = url_for('uploaded_file', filename=existing_file, _external=True)
                file_urls.append(file_url)
            else:
                # Save the new file with a unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                file_url = url_for('uploaded_file', filename=unique_filename, _external=True)
                file_urls.append(file_url)
        else:
            return jsonify({'error': f'File type not allowed for file: {file.filename}'}), 400

    return jsonify({'urls': file_urls}), 201

# API: Paste Submission
@api_bp.route('/paste', methods=['POST'])
def api_paste():
    data = request.get_json()
    content = data.get('content')

    if not content:
        return jsonify({'error': 'No content provided'}), 400

    # Create a unique ID for the paste
    paste_id = str(uuid.uuid4())
    paste_filename = f"{paste_id}.txt"
    paste_path = os.path.join(PASTEBIN_FOLDER, paste_filename)

    # Save the paste content to a file
    with open(paste_path, 'w') as f:
        f.write(content)

    # Return the URL to access the paste
    paste_url = url_for('view_paste', paste_id=paste_id, _external=True)
    return jsonify({'url': paste_url}), 201
