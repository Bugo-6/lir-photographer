from http.server import HTTPServer, BaseHTTPRequestHandler
import base64, os

GALLERY = os.path.join(os.path.dirname(__file__), 'gallery')
os.makedirs(GALLERY, exist_ok=True)

PAGE = b"""<!DOCTYPE html><html><body><script>
(async()=>{
  const raw = window.name;
  if(!raw||!raw.includes('|')){document.body.textContent='no data: '+raw.substring(0,50);return;}
  const idx = raw.indexOf('|');
  const filename = raw.substring(0,idx);
  const b64 = raw.substring(idx+1);
  window.name = '';
  const r = await fetch('http://localhost:8765/save',{method:'POST',body:filename+'|'+b64});
  const t = await r.text();
  document.body.textContent = 'saved: '+filename+' result:'+t;
})();
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type','text/html')
        self._cors()
        self.end_headers()
        self.wfile.write(PAGE)

    def do_POST(self):
        n = int(self.headers['Content-Length'])
        body = self.rfile.read(n).decode('utf-8')
        filename, b64 = body.split('|', 1)
        path = os.path.join(GALLERY, filename)
        with open(path, 'wb') as f:
            f.write(base64.b64decode(b64))
        print(f'Saved: {filename} ({os.path.getsize(path)//1024}KB)', flush=True)
        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(b'ok')

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')

    def log_message(self,*a): pass

print('Server ready on http://localhost:8765', flush=True)
HTTPServer(('localhost', 8765), Handler).serve_forever()
