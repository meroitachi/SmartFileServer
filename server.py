import http.server, socketserver, os, urllib.parse, zipfile, io, time

PORT = 8000

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def list_directory(self, path):
        try:
            list_dir = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

        list_dir.sort(key=lambda a: a.lower())
        displaypath = urllib.parse.unquote(self.path)
        enc = "utf-8"

        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>📁 Index of {displaypath}</title>
<style>
body {{
  font-family: "Segoe UI", sans-serif;
  background: #121212;
  color: #eee;
  margin: 0;
}}
h2 {{
  text-align: center;
  padding: 20px;
  margin: 0;
  background: #1e1e1e;
  box-shadow: 0 2px 4px #000a;
}}
table {{
  width: 96%;
  margin: 20px auto;
  border-collapse: collapse;
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
}}
th, td {{
  padding: 10px;
  border-bottom: 1px solid #333;
  text-align: left;
  white-space: nowrap;
}}
tr:hover {{
  background: #2a2a2a;
}}
.download-btn {{
  background: none;
  border: none;
  cursor: pointer;
  font-size: 22px;
  color: #00bfff;
  text-decoration: none;
}}
a {{
  text-decoration: none;
  color: #9cf;
}}
a:hover {{ color: #fff; }}
.drop {{
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: 0;
  width: 55px;
  height: 55px;
  background: radial-gradient(circle at 30% 30%, #00bfff, #0066aa);
  border-radius: 50% 50% 60% 60%;
  animation: dropFall 6s ease-in-out;
  box-shadow: 0 0 15px #00bfff;
  z-index: 9999;
}}
.drop::after {{
  content: "💧";
  position: absolute;
  top: 8px;
  left: 14px;
  font-size: 28px;
}}
@keyframes dropFall {{
  0% {{ bottom: 100%; opacity: 1; transform: translateX(-50%) scale(1); }}
  80% {{ bottom: 45px; opacity: 1; transform: translateX(-50%) scale(1.2); }}
  100% {{ bottom: 0; opacity: 0; transform: translateX(-50%) scale(0.9); }}
}}
.water {{
  position: fixed;
  bottom: 0;
  width: 100%;
  height: 35px;
  background: linear-gradient(to top, #003355, #0088cc);
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
}}
#popup {{
  position: fixed;
  bottom: 50px;
  left: 50%;
  transform: translateX(-50%);
  background: #222;
  color: #0ff;
  padding: 12px 20px;
  border-radius: 10px;
  box-shadow: 0 0 10px #00bfff99;
  font-size: 15px;
  display: none;
  z-index: 9999;
}}
</style>
<script>
function showDrop() {{
  const drop = document.createElement('div');
  drop.className = 'drop';
  document.body.appendChild(drop);
  setTimeout(() => drop.remove(), 6000);
}}
function showPopup(msg) {{
  const popup = document.getElementById('popup');
  popup.textContent = msg;
  popup.style.display = 'block';
}}
function hidePopup() {{
  const popup = document.getElementById('popup');
  setTimeout(() => popup.style.display = 'none', 4000);
}}
function startZipping() {{
  showPopup('🌀 Zipping folder... please wait');
  setTimeout(()=>showPopup('🧩 Compressing files...'),2000);
  setTimeout(()=>showPopup('✅ Ready to download!'),4500);
  setTimeout(()=>hidePopup(),6000);
  showDrop();
}}
</script>
</head><body>
<h2>📂 Index of {displaypath}</h2>
<table>
<tr><th>Name</th><th>Details</th><th>Action</th></tr>"""

        icons = {
            'folder': '📁', 'video': '🎬', 'image': '🖼️',
            'music': '🎵', 'pdf': '📖', 'text': '📄', 'code': '💻',
            'archive': '💾', 'excel': '📊', 'word': '📘', 'ppt': '📽️',
            'other': '📦'
        }

        for name in list_dir:
            fullname = os.path.join(path, name)
            displayname = linkname = name

            if os.path.isdir(fullname):
                sub_items = os.listdir(fullname)
                file_count = sum(os.path.isfile(os.path.join(fullname, i)) for i in sub_items)
                folder_count = sum(os.path.isdir(os.path.join(fullname, i)) for i in sub_items)
                info_text = f"{folder_count} folders, {file_count} files"
                icon = icons['folder']
                current_path = urllib.parse.quote(os.path.join(displaypath.strip("/"), linkname))
                html += f"""
<tr>
<td><a href="{urllib.parse.quote(linkname)}/">{icon} {displayname}/</a></td>
<td>{info_text}</td>
<td><a href="?download_folder={current_path}" onclick="startZipping()" class="download-btn" title="Download Folder as ZIP">⬇️</a></td>
</tr>"""
            else:
                ext = os.path.splitext(name)[1].lower()
                size = os.path.getsize(fullname)
                size_text = format_size(size)

                if ext in ('.mp4', '.mov', '.avi', '.mkv'): icon = icons['video']
                elif ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'): icon = icons['image']
                elif ext in ('.mp3', '.wav', '.ogg', '.flac'): icon = icons['music']
                elif ext == '.pdf': icon = icons['pdf']
                elif ext in ('.txt', '.md'): icon = icons['text']
                elif ext in ('.py', '.js', '.html', '.css', '.json'): icon = icons['code']
                elif ext in ('.zip', '.rar', '.tar', '.gz'): icon = icons['archive']
                elif ext in ('.xls', '.xlsx', '.csv'): icon = icons['excel']
                elif ext in ('.doc', '.docx'): icon = icons['word']
                elif ext in ('.ppt', '.pptx'): icon = icons['ppt']
                else: icon = icons['other']

                html += f"""
<tr>
<td><a href="{urllib.parse.quote(linkname)}">{icon} {displayname}</a></td>
<td>{size_text}</td>
<td><a href="{urllib.parse.quote(linkname)}" onclick="showDrop()" class="download-btn" download>⬇️</a></td>
</tr>"""

        html += """</table>
<div id='popup'></div>
<div class='water'></div>
</body></html>"""

        encoded = html.encode(enc, 'surrogateescape')
        self.send_response(200)
        self.send_header("Content-type", f"text/html; charset={enc}")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return io.BytesIO(encoded)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        if "download_folder" in query:
            rel_folder = query["download_folder"][0].lstrip("/")
            folder_path = os.path.join(os.getcwd(), rel_folder)
            if os.path.isdir(folder_path):
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(folder_path):
                        for f in files:
                            full_path = os.path.join(root, f)
                            rel_path = os.path.relpath(full_path, os.path.dirname(folder_path))
                            zipf.write(full_path, rel_path)
                            time.sleep(0.01)
                buffer.seek(0)
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(folder_path)}.zip"')
                self.end_headers()
                self.wfile.write(buffer.read())
                return

        return super().do_GET()

with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    print(f"🚀 Server running at http://localhost:{PORT}")
    httpd.serve_forever()
