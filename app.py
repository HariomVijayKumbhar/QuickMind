import os
import sys


backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app  # noqa: E402


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "10000"))

    reload = os.getenv("RELOAD", "False").lower() == "true"

    print(f"Starting server at http://{host}:{port}")

    uvicorn.run("main:app", host=host, port=port, reload=reload)
