"""Servidor local: sirve /frontend con respaldo a index.html y reenvía /api al backend.
Uso: python servir.py [puerto_frontend] [url_backend]
Ejemplo: python servir.py 3000 http://localhost:8000
"""
import mimetypes, os, sys, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
BACKEND = (sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000").rstrip("/")
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")


class H(BaseHTTPRequestHandler):
    def _proxy(self):
        n = int(self.headers.get("Content-Length") or 0)
        cuerpo = self.rfile.read(n) if n else None
        req = urllib.request.Request(BACKEND + self.path, data=cuerpo, method=self.command)
        for k in ("Content-Type", "Accept"):
            if self.headers.get(k):
                req.add_header(k, self.headers[k])
        try:
            r = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            r = e
        except Exception:
            self.send_error(502, "No se pudo conectar con el backend")
            return
        datos = r.read()
        self.send_response(r.status if hasattr(r, "status") else r.code)
        self.send_header("Content-Type", r.headers.get("Content-Type", "application/json"))
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(datos)

    def _estatico(self):
        ruta = self.path.split("?")[0]
        f = os.path.normpath(os.path.join(RAIZ, ruta.lstrip("/")))
        if not f.startswith(RAIZ) or not os.path.isfile(f):
            f = os.path.join(RAIZ, "index.html")
        with open(f, "rb") as fh:
            datos = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(f)[0] or "text/html")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def handle_any(self):
        (self._proxy if self.path.startswith("/api") else self._estatico)()

    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = handle_any


print(f"Interfaz en http://localhost:{PUERTO}  (API -> {BACKEND})")
ThreadingHTTPServer(("", PUERTO), H).serve_forever()
