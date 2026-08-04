from pathlib import Path

# backend/uploads/logs
UPLOAD_DIR = Path("uploads/raw")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)