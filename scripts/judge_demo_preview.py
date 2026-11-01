"""Build and serve a loopback-only demo with its own SQLite data and AI disabled."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8017)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use a local port between 1024 and 65535")
    root = Path(__file__).resolve().parents[1]
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm:
        parser.error("Install the project's Node dependencies before starting the preview")
    subprocess.run([npm, "run", "build"], cwd=root / "frontend", check=True)
    cache = root / ".cache"
    cache.mkdir(exist_ok=True)
    origin = f"http://127.0.0.1:{args.port}"
    os.environ.update(
        {
            "BRANDPROOF_DATABASE_URL": f"sqlite:///{(cache / 'judge-demo-preview.db').as_posix()}",
            "BRANDPROOF_FRONTEND_DIST": str(root / "frontend/dist"),
            "BRANDPROOF_PUBLIC_ORIGIN": origin,
            "BRANDPROOF_CORS_ORIGINS": json.dumps([origin, f"http://localhost:{args.port}"]),
            "BRANDPROOF_DEMO_COOKIE_SECURE": "false",  # Loopback HTTP only.
            "BRANDPROOF_EXTERNAL_AI_ENABLED": "false",
            "BRANDPROOF_AI_PROVIDER": "none",
            "BRANDPROOF_DEMO_SESSIONS_HOURLY_LIMIT": "20",
            "BRANDPROOF_DEMO_OPERATIONS_HOURLY_LIMIT": "300",
        }
    )
    tesseract = Path("C:/Program Files/Tesseract-OCR")
    if os.name == "nt" and (tesseract / "tesseract.exe").is_file():
        os.environ["PATH"] = str(tesseract) + os.pathsep + os.environ["PATH"]
    import uvicorn

    uvicorn.run(
        "brandproof.main:create_app",
        factory=True,
        host="127.0.0.1",
        port=args.port,
        workers=1,
        access_log=False,
    )


if __name__ == "__main__":
    main()
