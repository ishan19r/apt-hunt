#!/usr/bin/env python3
"""Apartment Tracker & Response Generator"""
import json
from datetime import datetime
import os

TRACKER_FILE = "tracked_apartments.json"
PROFILE = {"name": "Ishan", "email": "ishan.19r@gmail.com", "income": 110000}

def load_tracker():
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {"apartments": []}

def save_tracker(data):
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_apartment(address, rent, neighborhood, url, broker=None, notes=None):
    tracker = load_tracker()
    apt = {"id": len(tracker["apartments"]) + 1, "address": address, "rent": rent, "neighborhood": neighborhood, "url": url, "broker": broker, "notes": notes, "added": datetime.now().isoformat(), "status": "interested", "40x_pass": PROFILE["income"] >= rent * 40}
    tracker["apartments"].append(apt)
    save_tracker(tracker)
    return apt

def generate_inquiry(address):
    return f"Hi,\n\nI'm interested in the 1-bedroom at {address}.\n\n1. Is the unit still available?\n2. Any additional fees?\n3. Income/credit requirements?\n4. Any flexibility on lease terms?\n\nAvailable weekdays after 5:30pm or weekends.\n\nThanks!\nIshan"

def generate_schedule_response(broker, method="facetime"):
    if method == "facetime":
        return f"Hi {broker},\n\nThanks for getting back to me! I can't make weekday mornings since I'm working — would you be open to a quick FaceTime tour instead?\n\nThanks!\nIshan"
    return f"Hi {broker},\n\nI'd love to see the unit. Available tomorrow after 5:30pm or this weekend anytime.\n\nThanks!\nIshan"

def generate_negotiation(broker, target_rent):
    return f"Hi {broker},\n\nThanks for showing me the apartment! I'm very interested. Would you be open to ${target_rent:,}/month? I'm ready to sign quickly.\n\nThanks!\nIshan"

def show_apartments():
    tracker = load_tracker()
    for apt in tracker["apartments"]:
        status = "✅" if apt["40x_pass"] else "⚠️"
        print(f"#{apt['id']} {apt['address']} - ${apt['rent']:,}/mo {status} [{apt['status']}]")

if __name__ == "__main__":
    print("🏠 APARTMENT TRACKER\n")
    show_apartments()
