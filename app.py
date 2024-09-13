from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, abort
import os
import uuid
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from mimetypes import guess_type
import pytz
from api import api_bp  # Import the API blueprint

app = Flask(__name__)

# Configurations
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PASTEBIN_FOLDER'] = 'pastes'
app.config['ALLOWED_EXTENSIONS'] = {
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg', 'webp',
    'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', '3gp',
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'rtf',
    'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma',
    'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz',
    'py', 'js', 'html', 'css', 'php', 'java', 'c', 'cpp', 'h', 'hpp', 'xml', 'json', 'yaml', 'csv'
}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB
app.config['FILE_EXPIRATION_TIME'] = timedelta(days=1)  # Files expire after 1 day

# Timezone configuration
timezone = pytz.timezone('UTC')  # or your desired timezone

# Ensure upload and pastebin folders exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['PASTEBIN_FOLDER']):
    os.makedirs(app.config['PASTEBIN_FOLDER'])

# Helper function to check for allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Scheduler to delete expired files
def delete_expired_files():
    now = datetime.now()
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path):
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if now - file_creation_time > app.config['FILE_EXPIRATION_TIME']:
                os.remove(file_path)
                print(f"Deleted expired file: {filename}")

# Start the scheduler for deleting expired files every hour
scheduler = BackgroundScheduler(timezone=timezone)
scheduler.add_job(delete_expired_files, 'interval', hours=1)
scheduler.start()

# Register the API blueprint
app.register_blueprint(api_bp, url_prefix='/api')

# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for serving uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        mime_type, _ = guess_type(file_path)
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, mimetype=mime_type)
    else:
        return abort(404)

# Route to view a paste by ID
@app.route('/pastebin/<paste_id>')
def view_paste(paste_id):
    paste_path = os.path.join(app.config['PASTEBIN_FOLDER'], f"{paste_id}.txt")

    if not os.path.exists(paste_path):
        return jsonify({'error': 'Paste not found'}), 404

    with open(paste_path, 'r') as f:
        content = f.read()

    # Pass both content and paste_id to the template
    return render_template('view_paste.html', content=content, paste_id=paste_id)

# Route to view a paste as raw text
@app.route('/pastebin/<paste_id>/raw')
def view_paste_raw(paste_id):
    paste_path = os.path.join(app.config['PASTEBIN_FOLDER'], f"{paste_id}.txt")

    if not os.path.exists(paste_path):
        return jsonify({'error': 'Paste not found'}), 404

    # Serve the raw text content
    return send_from_directory(app.config['PASTEBIN_FOLDER'], f"{paste_id}.txt", mimetype='text/plain')

@app.route('/faq')
def faq():
    return render_template('faq.html')


# Start the Flask application
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8866, debug=True)
