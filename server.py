from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import shutil
import time

app = Flask(__name__, static_folder='.')
CORS(app)

BASE_DIR = os.path.abspath('files')  # كل الملفات ستكون داخل هذا المجلد

def safe_join(base, *paths):
    # حماية من المسارات الخبيثة
    final_path = os.path.abspath(os.path.join(base, *paths))
    if not final_path.startswith(base):
        raise ValueError("Invalid path")
    return final_path

@app.route('/api/list')
def list_files():
    rel_path = request.args.get('path', '').strip('/')
    abs_path = safe_join(BASE_DIR, rel_path)
    folders, files = [], []
    if os.path.exists(abs_path):
        for entry in os.listdir(abs_path):
            full = os.path.join(abs_path, entry)
            if os.path.isdir(full):
                folders.append(entry)
            else:
                files.append(entry)
    return jsonify({'folders': sorted(folders), 'files': sorted(files)})

@app.route('/api/create_folder', methods=['POST'])
def create_folder():
    data = request.json
    rel_path = data.get('path', '').strip('/')
    name = data.get('name')
    abs_path = safe_join(BASE_DIR, rel_path, name)
    os.makedirs(abs_path, exist_ok=True)
    return jsonify({'success': True})

@app.route('/api/delete', methods=['POST'])
def delete():
    data = request.json
    rel_path = data.get('path', '').strip('/')
    name = data.get('name')
    is_folder = data.get('is_folder')
    abs_path = safe_join(BASE_DIR, rel_path, name)
    if is_folder:
        shutil.rmtree(abs_path, ignore_errors=True)
    else:
        if os.path.exists(abs_path):
            os.remove(abs_path)
    return jsonify({'success': True})

@app.route('/api/rename', methods=['POST'])
def rename():
    data = request.json
    rel_path = data.get('path', '').strip('/')
    name = data.get('name')
    new_name = data.get('new_name')
    abs_path = safe_join(BASE_DIR, rel_path, name)
    new_path = safe_join(BASE_DIR, rel_path, new_name)
    os.rename(abs_path, new_path)
    return jsonify({'success': True})

@app.route('/api/move', methods=['POST'])
def move():
    data = request.json
    rel_path = data.get('path', '').strip('/')
    name = data.get('name')
    dest = data.get('dest', '').strip('/')
    abs_path = safe_join(BASE_DIR, rel_path, name)
    dest_path = safe_join(BASE_DIR, dest, name)
    shutil.move(abs_path, dest_path)
    return jsonify({'success': True})

@app.route('/api/upload', methods=['POST'])
def upload():
    file = request.files['file']
    rel_path = request.form.get('path', '').strip('/')
    abs_path = safe_join(BASE_DIR, rel_path, file.filename)
    file.save(abs_path)
    return jsonify({'success': True})

@app.route('/api/download')
def download():
    rel_path = request.args.get('path', '').strip('/')
    name = request.args.get('name')
    abs_path = safe_join(BASE_DIR, rel_path)
    return send_from_directory(abs_path, name, as_attachment=True)

@app.route('/api/copy', methods=['POST'])
def copy():
    data = request.json
    rel_path = data.get('path', '').strip('/')
    name = data.get('name')
    dest = data.get('dest', '').strip('/')
    is_folder = data.get('is_folder')
    src_path = safe_join(BASE_DIR, rel_path, name)
    dest_path = safe_join(BASE_DIR, dest, name)
    if is_folder:
        shutil.copytree(src_path, dest_path)
    else:
        shutil.copy2(src_path, dest_path)
    return jsonify({'success': True})

@app.route('/api/details')
def details():
    rel_path = request.args.get('path', '').strip('/')
    name = request.args.get('name')
    is_folder = request.args.get('is_folder') == 'true'
    abs_path = safe_join(BASE_DIR, rel_path, name)
    stat = os.stat(abs_path)
    size = stat.st_size if not is_folder else sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, dn, filenames in os.walk(abs_path)
        for f in filenames
    )
    created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_ctime))
    modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
    return jsonify({'size': size, 'created': created, 'modified': modified})

@app.route('/api/preview')
def preview():
    rel_path = request.args.get('path', '').strip('/')
    name = request.args.get('name')
    abs_path = safe_join(BASE_DIR, rel_path, name)
    try:
        with open(abs_path, encoding='utf-8') as f:
            content = f.read(5000)
        return content
    except Exception:
        return 'لا يمكن عرض هذا الملف', 400

@app.route('/api/embed_youtube', methods=['POST'])
def embed_youtube():
    data = request.json
    rel_path = data.get('path', '').strip('/')
    folder = data.get('folder')
    url = data.get('url')
    folder_path = safe_join(BASE_DIR, rel_path, folder)
    os.makedirs(folder_path, exist_ok=True)
    with open(os.path.join(folder_path, 'youtube_embed.txt'), 'w', encoding='utf-8') as f:
        f.write(url.strip())
    return jsonify({'success': True})

@app.route('/api/youtube_embed')
def youtube_embed():
    rel_path = request.args.get('path', '').strip('/')
    abs_path = safe_join(BASE_DIR, rel_path, 'youtube_embed.txt')
    if os.path.exists(abs_path):
        with open(abs_path, encoding='utf-8') as f:
            return f.read()

@app.route('/')
def root():
    # عرض الصفحة الرئيسية index.html
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    # عرض لوحة التحكم admin.html
    return send_from_directory('.', 'admin.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # لخدمة ملفات html أو ملفات ثابتة أخرى مباشرة
    file_path = os.path.join('.', filename)
    if os.path.isfile(file_path):
        return send_from_directory('.', filename)
    return "Not Found", 404

if __name__ == '__main__':
    os.makedirs(BASE_DIR, exist_ok=True)
    app.run(debug=True)
