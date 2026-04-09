from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import mimetypes
from urllib.parse import urlparse

from parser import construir_demo_lr1


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
GRAMMAR_FILE = BASE_DIR / "gramatica.txt"


class LR1RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/demo":
            self.handle_demo()
            return

        self.handle_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/parse":
            self.handle_parse()
            return

        self.send_json({"error": "Ruta no encontrada"}, status=404)

    def handle_demo(self):
        try:
            datos = construir_demo_lr1(str(GRAMMAR_FILE), ["id", "+", "id", "*", "id"])
            self.send_json(datos)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)

    def handle_parse(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            payload = json.loads(body.decode("utf-8"))
            tokens = payload.get("tokens", [])
            if not isinstance(tokens, list):
                self.send_json({"error": "El campo 'tokens' debe ser una lista"}, status=400)
                return

            datos = construir_demo_lr1(str(GRAMMAR_FILE), tokens)
            self.send_json(datos)
        except json.JSONDecodeError:
            self.send_json({"error": "JSON invalido"}, status=400)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)

    def handle_static(self, path):
        if path in ("", "/"):
            path = "/index.html"

        target = (WEB_DIR / path.lstrip("/")).resolve()

        if WEB_DIR not in target.parents and target != WEB_DIR:
            self.send_json({"error": "Ruta invalida"}, status=403)
            return

        if not target.exists() or not target.is_file():
            self.send_json({"error": "Archivo no encontrado"}, status=404)
            return

        mime_type, _ = mimetypes.guess_type(str(target))
        mime_type = mime_type or "application/octet-stream"

        with open(target, "rb") as f:
            contenido = f.read()

        self.send_response(200)
        self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def send_json(self, data, status=200):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def run_server(host="127.0.0.1", port=8000):
    server = HTTPServer((host, port), LR1RequestHandler)
    print(f"Servidor LR(1) en http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
