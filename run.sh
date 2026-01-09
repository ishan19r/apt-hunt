#!/bin/bash
echo "============================================================"
echo "   APARTMENT HUNTER PRO v2.0"
echo "============================================================"
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""
echo "Starting server..."
echo "   Open in browser: http://localhost:5000"
echo "============================================================"
python app.py
