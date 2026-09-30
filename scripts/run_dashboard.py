#!/usr/bin/env python3
"""
Launcher script for the Myntra Discovery Engine Dashboard.
Starts the FastAPI server with uvicorn.

Usage:
    python scripts/run_dashboard.py
    python scripts/run_dashboard.py --port 8000 --reload
"""

import argparse
import os
import sys
from pathlib import Path
import uvicorn

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    default_host = os.environ.get("HOST", "127.0.0.1")
    default_port = int(os.environ.get("PORT", "8000"))

    parser = argparse.ArgumentParser(description="Run Myntra Discovery Engine Dashboard")
    parser.add_argument("--host", type=str, default=default_host, help=f"Host to bind (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port to bind (default: {default_port})")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    print("=" * 60)
    print("GOOGLE PHOTOS DISCOVERY ENGINE & RETRIEVAL MVP")
    print("=" * 60)
    print(f"🚀 Server running at: http://{args.host}:{args.port}")
    print(f"📊 API Documentation: http://{args.host}:{args.port}/docs")
    print("=" * 60)

    uvicorn.run(
        "dashboard.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
