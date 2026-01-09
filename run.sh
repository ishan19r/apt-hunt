#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""
echo "Starting Apartment Hunter..."
echo "Open http://localhost:5000 in your browser"
echo ""
python app.py
