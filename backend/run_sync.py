"""
Manual one-shot sync runner for Uybor.uz marketplace.

Usage:
    cd backend
    python run_sync.py
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tasks.uybor_sync import sync_uybor_listings

if __name__ == "__main__":
    print("Starting Uybor.uz sync...")
    asyncio.run(sync_uybor_listings())
    print("Done.")
