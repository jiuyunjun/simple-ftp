from flask import Flask, request, send_from_directory, render_template_string, send_file
import os
import datetime
import json
import random
import shutil
import zipfile
import io
import logging

app = Flask(__name__)
BASE_UPLOAD_FOLDER = 'uploads'
TEMP_UPLOAD_FOLDER = 'temp_uploads'
GLOBAL_META_FILE = 'global_metadata.json'
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
META_FILE_NAME = 'metadata.json'
COMMENTS_FILE_NAME = 'comments.json'
META_FOLDER_NAME = '.meta'
VERSIONS_FOLDER_NAME = '.versions'
LOG_FILE = 'server.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    filename=LOG_FILE,
    encoding='utf-8'
)

# Load global metadata if exists
if os.path.exists(GLOBAL_META_FILE):
    with open(GLOBAL_META_FILE, 'r',encoding='utf-8') as f:
        global_metadata = json.load(f)
else:
    global_metadata = {}

def get_background_color(ip):
    if ip not in global_metadata:
        color = "#%06x" % random.randint(0, 0xFFFFFF)
        global_metadata[ip] = color
        with open(GLOBAL_META_FILE, 'w',encoding='utf-8') as f:
            json.dump(global_metadata, f, ensure_ascii=False, indent=4)
    return global_metadata[ip]

def get_text_color(hex_color):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    brightness = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return '#FFFFFF' if brightness < 0.5 else '#000000'

app.jinja_env.globals.update(get_text_color=get_text_color)

def log_action(ip, action):
    """Record an action performed by an IP."""
    logging.info(f"{ip} {action}")

def archive_file(upload_folder, filename):
    """Save current version of a file before overwriting or deleting."""
    src = os.path.join(upload_folder, filename)
    if not os.path.exists(src):
        return
    versions_dir = os.path.join(upload_folder, VERSIONS_FOLDER_NAME, filename)
    os.makedirs(versions_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.move(src, os.path.join(versions_dir, f'{timestamp}_{filename}'))

@app.route('/<username>/')
def index(username):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    os.makedirs(upload_folder, exist_ok=True)
    meta_folder = os.path.join(upload_folder, META_FOLDER_NAME)
    os.makedirs(meta_folder, exist_ok=True)
    meta_file = os.path.join(meta_folder, META_FILE_NAME)
    comments_file = os.path.join(meta_folder, COMMENTS_FILE_NAME)
    
    # Load metadata if exists
    if os.path.exists(meta_file):
        with open(meta_file, 'r',encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = {}

    files = {fname: meta for fname, meta in metadata.items()
             if os.path.exists(os.path.join(upload_folder, fname))}
    
    # Load comments if exists
    if os.path.exists(comments_file):
        with open(comments_file, 'r',encoding='utf-8') as f:
            comments = json.load(f)
    else:
        comments = []

    log_action(request.remote_addr, f"view index for {username}")

    reverse_comments = request.args.get('reverse_comments', 'false').lower() == 'true'
    if reverse_comments:
        comments = comments[::-1]
    
    message = request.args.get('message')
    return render_template_string('''
    <!doctype html>
    <html>
    <head>
      <title>File Sharing</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta charset="utf-8">
      <link rel="icon" href="{{ url_for('static', filename='favicons/favicon.ico') }}" type="image/x-icon">
      <style>
        .disabled-upload-button {
          background-color: #e0e0e0;
          cursor: not-allowed; opacity: 0.6;
        }
        .disabled-upload-button:enabled {
          background-color: #007bff;
          cursor: pointer;
        }
        body {
          font-family: Arial, sans-serif;
          background-color: #f0f2f5;
          color: #333;
          padding: 20px;
          margin: 0;
        }
        h1 {
          color: #007bff;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 20px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        table, th, td {
          border: 1px solid #ddd;
        }
        th, td {
          padding: 12px;
          text-align: left;
        }
        th {
          background-color: #007bff;
          color: white;
        }
        input[type="file"] {
          margin-bottom: 10px;
        }
        textarea {
          width: 100%;
          margin-bottom: 10px;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 5px;
        }
        button, input[type="submit"] {
          background-color: #007bff;
          color: white;
          border: none;
          padding: 10px 15px;
          margin: 5px 0;
          cursor: pointer;
          border-radius: 5px;
          transition: background-color 0.3s;
        }
        button:hover, input[type="submit"]:hover {
          background-color: #0056b3;
        }
        .comment-item {
          word-wrap: break-word;
          padding: 15px;
          margin: 10px 0;
          border: 1px solid #ddd;
          border-radius: 10px;
          background-color: #ffffff;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .copy-message {
          position: fixed;
          bottom: 20px;
          left: 50%;
          transform: translateX(-50%);
          background-color: #4caf50;
          color: white;
          padding: 10px;
          border-radius: 5px;
          z-index: 1000;
        }
        .file-actions a {
          color: #007bff;
          text-decoration: none;
        }
        .file-actions a:hover {
          text-decoration: underline;
        }
        .drop-area {
          border: 2px dashed #007bff;
          padding: 20px;
          text-align: center;
          margin-bottom: 10px;
          color: #666;
        }
        .drop-area.dragover {
          background-color: #e6f7ff;
          border-color: #1890ff;
          color: #000;
        }
        .selected-row {
          background-color: #d0e8ff;
        }
      </style>
    </head>
    <body>
    <h1>Upload a File or Folder</h1>
    <h2>Upload Individual File</h2>
    <form id="fileUploadForm" method=post enctype=multipart/form-data action="/{{ username }}/upload_file">
      <input type=file name=file id=fileInput multiple onchange="checkFile()">
      <input type=submit value=Upload id=uploadButton disabled class="disabled-upload-button">
      <progress id="uploadProgress" value="0" max="100" style="display:none;width:100%;"></progress>
    </form>
    <h2>Drag &amp; Drop Upload</h2>
    <div id="dropArea" class="drop-area">Drag files here</div>
    <h2>Upload Folder</h2>
    <form id="folderUploadForm" method=post enctype=multipart/form-data action="/{{ username }}/upload_folder">
      <input type=file name=file id=folderInput webkitdirectory mozdirectory multiple onchange="checkFolder()">
      <input type=submit value="Upload Folder" id=uploadFolderButton disabled class="disabled-upload-button">
      <progress id="folderUploadProgress" value="0" max="100" style="display:none;width:100%;"></progress>
    </form>
    <h1>Download Files</h1>
    <form id="batchDownloadForm" method=post action="/{{ username }}/download_batch">
    <table id="fileTable">
      <tr>
        <th>Filename</th>
        <th>Upload Time</th>
        <th>Upload IP</th>
        <th>Actions</th>
      </tr>
      {% for filename, meta in files.items() %}
      <tr data-filename="{{ filename }}" onclick="toggleRowSelection(event, this)">
        <td>{{ filename }}</td>
        <td>{{ meta['upload_time'] }}</td>
        <td>{{ meta['upload_ip'] }}</td>
        <td><a href="/{{ username }}/download/{{ filename }}">Download</a> - <a href="#" onclick="confirmDeletion('{{ filename }}')">Delete</a> - <a href="/{{ username }}/history/{{ filename }}">History</a></td>
      </tr>
      {% endfor %}
    </table>
    <input type=submit value="Download Selected" id="downloadSelectedButton" disabled class="disabled-upload-button">
    </form>
    <form method=post action="/{{ username }}/clear">
      <input type=submit value="Clear All Files" onclick="return confirm('Are you sure you want to delete all files?');">
    </form>
    <h1>Message Board</h1>
    <form method=post action="/{{ username }}/comment">
      <textarea name="comment" rows="4" cols="50" placeholder="Write your message here..."></textarea><br>
      <input type=submit value="Post Comment">
    </form>
    <h2>Comments</h2>
    
    <button onclick="toggleAllComments(true)">Expand All</button>
    <button onclick="toggleAllComments(false)">Collapse All</button>
    <button onclick="reverseComments()">Reverse Order</button>
    
    <ul>
        {% for comment in comments %}
        <li class="comment-item file-actions" ondblclick="toggleComment('{{ loop.index0 }}')" style="background-color: {{ comment['color'] }}; color: {{ get_text_color(comment['color']) }};">
        {{ comment['time'] }} - {{ comment['ip'] }}: 
        <button onclick="confirmCommentDeletion('{{ loop.index }}')">Delete</button>
        -  
        <button onclick='copyToClipboard({{ comment["text"] | tojson | safe }})'>Copy</button>
        <div id="comment-{{ loop.index0 }}" style="display:block;">
            <pre>{{ comment['text'] }}</pre>
        </div>
        </li>
        {% endfor %}
    </ul>
    <script>
      function toggleAllComments(expand) {
        const comments = document.querySelectorAll('[id^="comment-"]');
        comments.forEach(comment => {
          comment.style.display = expand ? 'block' : 'none';
        });
      }
    </script>
    <script>
      function toggleComment(index) {
        const commentDiv = document.getElementById('comment-' + index);
        if (commentDiv.style.display === 'none') {
          commentDiv.style.display = 'block';
        } else {
          commentDiv.style.display = 'none';
        }
      }
    </script>
    <script>
function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    // Modern approach using Clipboard API
    navigator.clipboard.writeText(text).then(function() {
      showCopyMessage('Comment copied to clipboard!');
    }).catch(function(err) {
      alert('Failed to copy comment: ' + err);
    });
  } else {
    // Fallback approach for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed'; // Avoid scrolling to bottom
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      showCopyMessage('Comment copied to clipboard!');
    } catch (err) {
      alert('Failed to copy comment: ' + err);
    }
    document.body.removeChild(textArea);
  }
}

function showCopyMessage(message) {
  const copyMessage = document.createElement('div');
  copyMessage.textContent = message;
  copyMessage.className = 'copy-message';
  document.body.appendChild(copyMessage);
  copyMessage.style.position = 'fixed';
  copyMessage.style.bottom = '20px';
  copyMessage.style.left = '50%';
  copyMessage.style.transform = 'translateX(-50%)';
  copyMessage.style.backgroundColor = '#4caf50';
  copyMessage.style.color = 'white';
  copyMessage.style.padding = '10px';
  copyMessage.style.borderRadius = '5px';
  copyMessage.style.zIndex = '1000';
  setTimeout(function() {
    document.body.removeChild(copyMessage);
  }, 2000);
}

    </script>
    <script>
      function confirmDeletion(filename) {
        if (confirm('Are you sure you want to delete ' + filename + '?')) {
          window.location.href = '/{{ username }}/delete/' + filename;
        }
      }
      function confirmCommentDeletion(commentIndex) {
        if (confirm('Are you sure you want to delete this comment?')) {
          const currentUrl = new URL(window.location.href);
          const reverseComments = currentUrl.searchParams.get('reverse_comments') === 'true';
          const adjustedIndex = reverseComments ? {{ comments|length }} - commentIndex : commentIndex - 1;
          window.location.href = '/{{ username }}/delete_comment/' + adjustedIndex;
        }
      }
      function checkFile() {
        const fileInput = document.getElementById('fileInput');
        const uploadButton = document.getElementById('uploadButton');
        if (fileInput.files.length > 0) {
          uploadButton.disabled = false;
          uploadButton.classList.remove('disabled-upload-button');
        } else {
          uploadButton.disabled = true;
          uploadButton.classList.add('disabled-upload-button');
        }
      }
      function checkFolder() {
        const folderInput = document.getElementById('folderInput');
        const uploadFolderButton = document.getElementById('uploadFolderButton');
        if (folderInput.files.length > 0) {
          uploadFolderButton.disabled = false;
          uploadFolderButton.classList.remove('disabled-upload-button');
        } else {
          uploadFolderButton.disabled = true;
          uploadFolderButton.classList.add('disabled-upload-button');
        }
      }
      function reverseComments() {
        const currentUrl = new URL(window.location.href);
        const reverseComments = currentUrl.searchParams.get('reverse_comments');
        currentUrl.searchParams.set('reverse_comments', reverseComments === 'true' ? 'false' : 'true');
        window.location.href = currentUrl.toString();
      }

      const selectedFiles = new Set();

      function toggleRowSelection(event, row) {
        if (event.target.tagName.toLowerCase() === 'a' || event.target.tagName.toLowerCase() === 'button') {
          return;
        }
        const fname = row.dataset.filename;
        if (selectedFiles.has(fname)) {
          selectedFiles.delete(fname);
          row.classList.remove('selected-row');
        } else {
          selectedFiles.add(fname);
          row.classList.add('selected-row');
        }
        updateDownloadButton();
      }

      function updateHiddenInputs() {
        const form = document.getElementById('batchDownloadForm');
        form.querySelectorAll('input[name="files"]').forEach(el => el.remove());
        selectedFiles.forEach(f => {
          const input = document.createElement('input');
          input.type = 'hidden';
          input.name = 'files';
          input.value = f;
          form.appendChild(input);
        });
      }

      function updateDownloadButton() {
        const btn = document.getElementById('downloadSelectedButton');
        const has = selectedFiles.size > 0;
        btn.disabled = !has;
        if (has) {
          btn.classList.remove('disabled-upload-button');
        } else {
          btn.classList.add('disabled-upload-button');
        }
        updateHiddenInputs();
      }

      const username = "{{ username }}";

      function uploadFiles(files) {
        if (files.length === 0) return;
        const formData = new FormData();
        for (const file of files) {
          formData.append('file', file);
        }
        const progress = document.getElementById('uploadProgress');
        progress.value = 0;
        progress.style.display = 'block';
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/${username}/upload_file`);
        xhr.upload.onprogress = function(event) {
          if (event.lengthComputable) {
            progress.value = (event.loaded / event.total) * 100;
          }
        };
        xhr.onload = function() {
          if (xhr.status === 200) {
            window.location.href = `/${username}/?message=File upload completed successfully!`;
          } else {
            alert('Upload failed');
          }
        };
        xhr.send(formData);
      }

      document.getElementById('fileUploadForm').addEventListener('submit', function(e) {
        e.preventDefault();
        uploadFiles(document.getElementById('fileInput').files);
      });

      const dropArea = document.getElementById('dropArea');
      dropArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropArea.classList.add('dragover');
      });
      dropArea.addEventListener('dragleave', function() {
        dropArea.classList.remove('dragover');
      });
      function uploadFolder(files) {
        if (files.length === 0) return;
        const formData = new FormData();
        for (const file of files) {
          formData.append('file', file);
        }
        const progress = document.getElementById('folderUploadProgress');
        progress.style.display = 'block';
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/${username}/upload_folder`);
        xhr.upload.onprogress = function(event) {
          if (event.lengthComputable) {
            progress.value = (event.loaded / event.total) * 100;
          }
        };
        xhr.onload = function() {
          if (xhr.status === 200) {
            window.location.href = `/${username}/?message=Folder upload completed successfully!`;
          } else {
            alert('Upload failed');
          }
        };
        xhr.send(formData);
      }
      dropArea.addEventListener('drop', function(e) {
        e.preventDefault();
        dropArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        let hasFolder = false;
        for (const f of files) {
          if (f.webkitRelativePath && f.webkitRelativePath.includes('/')) {
            hasFolder = true;
            break;
          }
        }
        if (hasFolder) {
          uploadFolder(files);
        } else {
          uploadFiles(files);
        }
      });

      document.getElementById('folderUploadForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const files = document.getElementById('folderInput').files;
        uploadFolder(files);
      });
      updateDownloadButton();
    </script>
    {% if message %}
    <script>alert("{{ message }}");</script>
    {% endif %}
    </body>
    </html>
    ''', files=files, comments=comments, username=username)

@app.route('/<username>/upload_file', methods=['POST'])
def upload_file(username):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    os.makedirs(upload_folder, exist_ok=True)
    meta_folder = os.path.join(upload_folder, META_FOLDER_NAME)
    os.makedirs(meta_folder, exist_ok=True)
    meta_file = os.path.join(meta_folder, META_FILE_NAME)
    os.makedirs(os.path.join(upload_folder, VERSIONS_FOLDER_NAME), exist_ok=True)
    
    if 'file' not in request.files:
        log_action(request.remote_addr, f"upload_file missing file part for {username}")
        return 'No file part'
    
    files = request.files.getlist('file')
    if len(files) == 0 or files[0].filename == '':
        log_action(request.remote_addr, f"upload_file no selected file for {username}")
        return 'No selected file'
    
    for file in files:
        filename = file.filename
        file_path = os.path.join(upload_folder, filename)
        if os.path.exists(file_path):
            archive_file(upload_folder, filename)
        file.save(file_path)
        log_action(request.remote_addr, f"uploaded {filename} for {username}")
        
        # Load metadata
        if os.path.exists(meta_file):
            with open(meta_file, 'r',encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # Save metadata
        metadata[filename] = {
            'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            'upload_ip': request.remote_addr
        }
        with open(meta_file, 'w',encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False,indent=4)
    
    return f'<script>window.location.href = "/{username}/?message=File upload completed successfully!";</script>'

@app.route('/<username>/upload_folder', methods=['POST'])
def upload_folder(username):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    os.makedirs(upload_folder, exist_ok=True)
    meta_folder = os.path.join(upload_folder, META_FOLDER_NAME)
    os.makedirs(meta_folder, exist_ok=True)
    meta_file = os.path.join(meta_folder, META_FILE_NAME)
    os.makedirs(os.path.join(upload_folder, VERSIONS_FOLDER_NAME), exist_ok=True)
    
    if 'file' not in request.files:
        log_action(request.remote_addr, f"upload_folder missing file part for {username}")
        return 'No file part'
    
    files = request.files.getlist('file')
    if len(files) == 0 or files[0].filename == '':
        log_action(request.remote_addr, f"upload_folder no selected folder for {username}")
        return 'No selected folder'
    
    temp_folder = os.path.join(TEMP_UPLOAD_FOLDER, username)
    os.makedirs(temp_folder, exist_ok=True)

    for file in files:
        file_path = os.path.join(temp_folder, file.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
    
    # Create a ZIP file from the uploaded folder with the original folder name
    original_folder_name = os.path.commonpath([file.filename for file in files]).split(os.sep)[0]
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"{original_folder_name}_{timestamp}.zip"
    zip_filepath = os.path.join(upload_folder, zip_filename)
    if os.path.exists(zip_filepath):
        archive_file(upload_folder, zip_filename)
    shutil.make_archive(zip_filepath[:-4], 'zip', temp_folder)
    log_action(request.remote_addr, f"uploaded folder {zip_filename} for {username}")

    # Remove the temporary files
    shutil.rmtree(temp_folder)

    # Load metadata
    if os.path.exists(meta_file):
        with open(meta_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}
    
    # Save metadata
    metadata[zip_filename] = {
        'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
        'upload_ip': request.remote_addr
    }
    with open(meta_file, 'w',encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False)
    
    return f'<script>window.location.href = "/{username}/?message=Folder upload completed successfully!";</script>'

@app.route('/<username>/download/<filename>')
def download_file(username, filename):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    log_action(request.remote_addr, f"downloaded {filename} for {username}")
    return send_from_directory(upload_folder, filename)

@app.route('/<username>/download_batch', methods=['POST'])
def download_batch(username):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    selected_files = request.form.getlist('files')
    if not selected_files:
        log_action(request.remote_addr, f"download_batch with no selection for {username}")
        return f'<script>window.location.href = "/{username}/?message=No files selected!";</script>'

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w') as zf:
        for fname in selected_files:
            file_path = os.path.join(upload_folder, fname)
            if os.path.isfile(file_path):
                zf.write(file_path, arcname=fname)
    mem.seek(0)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_action(request.remote_addr, f"downloaded batch {selected_files} for {username}")
    return send_file(mem, download_name=f'selected_{timestamp}.zip', as_attachment=True, mimetype='application/zip')

@app.route('/<username>/history/<filename>')
def file_history(username, filename):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    versions_dir = os.path.join(upload_folder, VERSIONS_FOLDER_NAME, filename)
    if not os.path.isdir(versions_dir):
        return f'<script>window.location.href = "/{username}/?message=No history for {filename}!";</script>'
    versions = sorted(os.listdir(versions_dir), reverse=True)
    items = ''.join(f'<li>{v} - <a href="/{username}/restore/{filename}/{v}">Restore</a></li>' for v in versions)
    return f'<h1>History for {filename}</h1><ul>{items}</ul><a href="/{username}/">Back</a>'

@app.route('/<username>/restore/<filename>/<version>')
def restore_version(username, filename, version):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    versions_dir = os.path.join(upload_folder, VERSIONS_FOLDER_NAME, filename)
    version_path = os.path.join(versions_dir, version)
    if not os.path.exists(version_path):
        log_action(request.remote_addr, f"attempted restore of missing {filename} {version} for {username}")
        return f'<script>window.location.href = "/{username}/?message=Version not found!";</script>'
    if os.path.exists(os.path.join(upload_folder, filename)):
        archive_file(upload_folder, filename)
    shutil.move(version_path, os.path.join(upload_folder, filename))
    meta_folder = os.path.join(upload_folder, META_FOLDER_NAME)
    os.makedirs(meta_folder, exist_ok=True)
    meta_file = os.path.join(meta_folder, META_FILE_NAME)
    metadata = {}
    if os.path.exists(meta_file):
        with open(meta_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    metadata[filename] = {
        'upload_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
        'upload_ip': request.remote_addr
    }
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
    log_action(request.remote_addr, f"restored {filename} version {version} for {username}")
    return f'<script>window.location.href = "/{username}/?message=File restored successfully!";</script>'

@app.route('/<username>/delete/<filename>', methods=['GET'])
def delete_file(username, filename):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    meta_folder = os.path.join(upload_folder, META_FOLDER_NAME)
    meta_file = os.path.join(meta_folder, META_FILE_NAME)
    file_path = os.path.join(upload_folder, filename)

    if os.path.exists(file_path):
        archive_file(upload_folder, filename)
        # Remove metadata
        if os.path.exists(meta_file):
            with open(meta_file, 'r',encoding='utf-8') as f:
                metadata = json.load(f)
            if filename in metadata:
                del metadata[filename]
                with open(meta_file, 'w',encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=4)
        log_action(request.remote_addr, f"deleted {filename} for {username}")
        return f'<script>window.location.href = "/{username}/?message=File deleted successfully!";</script>'
    else:
        log_action(request.remote_addr, f"attempted delete of missing {filename} for {username}")
        return f'<script>window.location.href = "/{username}/?message=File not found!";</script>'

@app.route('/<username>/clear', methods=['POST'])
def clear_files(username):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    meta_folder = os.path.join(upload_folder, META_FOLDER_NAME)
    meta_file = os.path.join(meta_folder, META_FILE_NAME)

    # Delete all files in the folder
    for filename in os.listdir(upload_folder):
        if filename in (META_FOLDER_NAME, VERSIONS_FOLDER_NAME):
            continue
        file_path = os.path.join(upload_folder, filename)
        if os.path.isfile(file_path):
            archive_file(upload_folder, filename)
    
    # Clear metadata
    if os.path.exists(meta_file):
        os.remove(meta_file)
    
    log_action(request.remote_addr, f"cleared all files for {username}")
    return f'<script>window.location.href = "/{username}/?message=All files deleted successfully!";</script>'

@app.route('/<username>/comment', methods=['POST'])
def add_comment(username):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    meta_folder = os.path.join(upload_folder, META_FOLDER_NAME)
    os.makedirs(meta_folder, exist_ok=True)
    comments_file = os.path.join(meta_folder, COMMENTS_FILE_NAME)
    
    comment_text = request.form.get('comment')
    if not comment_text:
        log_action(request.remote_addr, f"attempted empty comment for {username}")
        return f'<script>window.location.href = "/{username}/?message=Comment cannot be empty!";</script>'
    
    # Load comments
    if os.path.exists(comments_file):
        with open(comments_file, 'r',encoding='utf-8') as f:
            comments = json.load(f)
    else:
        comments = []
    
    # Add new comment
    comments.append({
        'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip': request.remote_addr,
        'text': comment_text,
        'color': get_background_color(request.remote_addr)
    })
    
    # Save comments
    with open(comments_file, 'w',encoding='utf-8') as f:
        json.dump(comments, f, indent=4, ensure_ascii=False)
    log_action(request.remote_addr, f"added comment for {username}")
    
    return f'<script>window.location.href = "/{username}/?message=Comment added successfully!";</script>'

@app.route('/<username>/delete_comment/<int:comment_index>', methods=['GET'])
def delete_comment(username, comment_index):
    upload_folder = os.path.join(BASE_UPLOAD_FOLDER, username)
    meta_folder = os.path.join(upload_folder, META_FOLDER_NAME)
    comments_file = os.path.join(meta_folder, COMMENTS_FILE_NAME)
    
    # Load comments
    if os.path.exists(comments_file):
        with open(comments_file, 'r',encoding='utf-8') as f:
            comments = json.load(f)
    else:
        comments = []
    
    # Delete the specified comment
    if 0 <= comment_index < len(comments):
        del comments[comment_index]
        with open(comments_file, 'w',encoding='utf-8') as f:
            json.dump(comments, f, indent=4, ensure_ascii=False)
        log_action(request.remote_addr, f"deleted comment {comment_index} for {username}")
        return f'<script>window.location.href = "/{username}/?message=Comment deleted successfully!";</script>'
    else:
        log_action(request.remote_addr, f"attempted delete of missing comment {comment_index} for {username}")
        return f'<script>window.location.href = "/{username}/?message=Comment not found!";</script>'

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
