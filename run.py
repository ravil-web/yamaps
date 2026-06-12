from __future__ import annotations

import os
import threading
import webbrowser

import uvicorn
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    if os.getenv("OPEN_BROWSER", "1") == "1":
        browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
        threading.Timer(1.2, lambda: webbrowser.open(f"http://{browser_host}:{port}")).start()
    uvicorn.run("app.main:app", host=host, port=port)


if __name__ == "__main__":
    main()
