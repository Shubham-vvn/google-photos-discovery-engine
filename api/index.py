"""
Vercel Serverless Entrypoint for Myntra Discovery Engine Dashboard
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.api import app
