"""Export FastAPI OpenAPI schema to a JSON file.

Usage:
    python scripts/export_openapi.py [--output ../frontend/openapi.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ["DEBUG"] = "True"
os.environ.setdefault("SECRET_KEY", "export-openapi-placeholder-secret-key-12345678901234567890")

from app.main import app


def export_schema(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    output_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OpenAPI schema exported to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export FastAPI OpenAPI schema")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / ".." / "frontend" / "openapi.json",
        help="Path to output JSON file",
    )
    args = parser.parse_args()
    export_schema(args.output)


if __name__ == "__main__":
    main()
