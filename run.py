"""
SpendSmart - Personal Finance & Budget Tracker
Main Application Runner
Launches Flask server connecting frontend, backend, and database layers.
"""

import os
import sys

# Ensure root directory is in Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f" SpendSmart - Personal Finance & Budget Tracker")
    print(f" Web Server Running at: http://127.0.0.1:{port}")
    print(f" Press CTRL+C to quit")
    print(f"=======================================================\n")
    app.run(debug=True, host='0.0.0.0', port=port)
