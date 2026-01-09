#!/usr/bin/env python3
"""
Apartment Hunter Web App with Browser Automation
- Scrapes StreetEasy listings
- Filters by your criteria
- Sends automated inquiries via browser
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ishan-apt-hunter-2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Your criteria
CRITERIA = {
    "min_rent": 2400,
    "max_rent": 3200,
    "bedrooms": 1,
    "income": 110000,
    "neighborhoods": ["east-harlem", "yorkville", "upper-east-side", "harlem"],
    "no_fee_preferred": True
}

PROFILE = {
    "name": "Ishan",
    "email": "ishan.19r@gmail.com",
    "phone": "",
    "availability": "Weekdays after 5:30pm, weekends anytime"
}

TRACKER_FILE = "tracked_apartments.json"

def load_tracker():
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {"apartments": [], "sent_inquiries": []}

def save_tracker(data):
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def check_affordability(rent):
    return CRITERIA["income"] >= rent * 40

def calculate_budget(rent):
    take_home = 5250
    after_rent = take_home - rent
    return {
        "rent": rent,
        "utilities": 150,
        "groceries": 400,
        "transport": 132,
        "dining_out": min(500, max(0, after_rent - 682)),
        "savings": max(0, after_rent - 1182)
    }

def generate_inquiry(address, broker_name=None):
    name = broker_name if broker_name else ""
    greeting = f"Hi {name}," if name else "Hi,"
    return f"""{greeting}

I'm interested in the 1-bedroom at {address}. A few questions:

1. Is the unit still available for immediate move-in?
2. Are there any additional fees beyond rent (amenity fees, move-in fees, etc.)?
3. What are the income/credit requirements for approval?
4. Is there any flexibility on the lease terms?

I'd love to schedule a viewing at your earliest convenience. I'm available weekdays after 5:30pm or weekends anytime.

Thanks!
{PROFILE['name']}"""

@app.route('/')
def index():
    return render_template('index.html', criteria=CRITERIA, profile=PROFILE)

@app.route('/api/apartments', methods=['GET'])
def get_apartments():
    tracker = load_tracker()
    return jsonify(tracker['apartments'])

@app.route('/api/apartments', methods=['POST'])
def add_apartment():
    data = request.json
    tracker = load_tracker()
    
    apt = {
        "id": len(tracker["apartments"]) + 1,
        "address": data.get("address"),
        "rent": int(data.get("rent", 0)),
        "neighborhood": data.get("neighborhood"),
        "url": data.get("url"),
        "broker_name": data.get("broker_name"),
        "broker_email": data.get("broker_email"),
        "notes": data.get("notes"),
        "image_url": data.get("image_url"),
        "added": datetime.now().isoformat(),
        "status": "new",
        "selected": False,
        "40x_pass": check_affordability(int(data.get("rent", 0))),
        "budget": calculate_budget(int(data.get("rent", 0)))
    }
    
    tracker["apartments"].append(apt)
    save_tracker(tracker)
    return jsonify(apt)

@app.route('/api/apartments/<int:apt_id>/select', methods=['POST'])
def toggle_select(apt_id):
    tracker = load_tracker()
    for apt in tracker["apartments"]:
        if apt["id"] == apt_id:
            apt["selected"] = not apt.get("selected", False)
            save_tracker(tracker)
            return jsonify(apt)
    return jsonify({"error": "Not found"}), 404

@app.route('/api/apartments/<int:apt_id>', methods=['DELETE'])
def delete_apartment(apt_id):
    tracker = load_tracker()
    tracker["apartments"] = [a for a in tracker["apartments"] if a["id"] != apt_id]
    save_tracker(tracker)
    return jsonify({"success": True})

@app.route('/api/inquiry/<int:apt_id>', methods=['GET'])
def get_inquiry(apt_id):
    tracker = load_tracker()
    for apt in tracker["apartments"]:
        if apt["id"] == apt_id:
            msg = generate_inquiry(apt["address"], apt.get("broker_name"))
            return jsonify({"message": msg, "apartment": apt})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/criteria', methods=['GET'])
def get_criteria():
    return jsonify(CRITERIA)

@app.route('/api/criteria', methods=['PUT'])
def update_criteria():
    global CRITERIA
    data = request.json
    CRITERIA.update(data)
    return jsonify(CRITERIA)

@socketio.on('connect')
def handle_connect():
    emit('status', {'message': 'Connected to Apartment Hunter'})

@socketio.on('start_scrape')
def handle_scrape(data):
    """Start scraping StreetEasy in background thread"""
    emit('status', {'message': 'Starting apartment search...'})
    thread = threading.Thread(target=scrape_apartments, args=(data,))
    thread.start()

@socketio.on('send_inquiries')
def handle_send_inquiries(data):
    """Send inquiries to selected apartments"""
    apt_ids = data.get('apartment_ids', [])
    emit('status', {'message': f'Preparing to send {len(apt_ids)} inquiries...'})
    thread = threading.Thread(target=send_bulk_inquiries, args=(apt_ids,))
    thread.start()

def scrape_apartments(data):
    """Scrape StreetEasy listings using Selenium"""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
    import re
    
    socketio.emit('status', {'message': 'Launching browser...'})
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        neighborhoods = data.get('neighborhoods', CRITERIA['neighborhoods'])
        min_rent = data.get('min_rent', CRITERIA['min_rent'])
        max_rent = data.get('max_rent', CRITERIA['max_rent'])
        
        all_listings = []
        
        for neighborhood in neighborhoods:
            socketio.emit('status', {'message': f'Searching {neighborhood.replace("-", " ").title()}...'})
            
            url = f"https://streeteasy.com/for-rent/{neighborhood}/price:{min_rent}-{max_rent}%7Cbeds:1"
            socketio.emit('status', {'message': f'Loading: {url}'})
            
            try:
                driver.get(url)
                time.sleep(3)
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "listingCard"))
                )
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                listings = soup.find_all('div', class_='listingCard') or soup.find_all('article', {'data-testid': 'listing-card'})
                
                socketio.emit('status', {'message': f'Found {len(listings)} listings in {neighborhood}'})
                
                for listing in listings[:10]:
                    try:
                        # Extract listing details
                        address_elem = listing.find('address') or listing.find(class_=re.compile('address', re.I))
                        price_elem = listing.find(class_=re.compile('price', re.I))
                        link_elem = listing.find('a', href=re.compile('/rental/'))
                        img_elem = listing.find('img')
                        
                        address = address_elem.get_text(strip=True) if address_elem else "Unknown Address"
                        
                        price_text = price_elem.get_text(strip=True) if price_elem else "0"
                        rent = int(re.sub(r'[^\d]', '', price_text) or 0)
                        
                        url = "https://streeteasy.com" + link_elem['href'] if link_elem and link_elem.get('href') else ""
                        image_url = img_elem.get('src', '') if img_elem else ""
                        
                        if rent >= min_rent and rent <= max_rent:
                            apt_data = {
                                "address": address,
                                "rent": rent,
                                "neighborhood": neighborhood.replace("-", " ").title(),
                                "url": url,
                                "image_url": image_url,
                                "broker_name": "",
                                "notes": "Auto-scraped from StreetEasy",
                                "40x_pass": check_affordability(rent),
                                "budget": calculate_budget(rent)
                            }
                            all_listings.append(apt_data)
                            socketio.emit('listing_found', apt_data)
                    except Exception as e:
                        socketio.emit('status', {'message': f'Error parsing listing: {str(e)}'})
                        continue
                        
            except Exception as e:
                socketio.emit('status', {'message': f'Error loading {neighborhood}: {str(e)}'})
                continue
        
        driver.quit()
        
        # Save all listings
        tracker = load_tracker()
        existing_urls = {a.get('url') for a in tracker['apartments']}
        
        new_count = 0
        for listing in all_listings:
            if listing['url'] and listing['url'] not in existing_urls:
                listing['id'] = len(tracker['apartments']) + 1
                listing['added'] = datetime.now().isoformat()
                listing['status'] = 'new'
                listing['selected'] = False
                tracker['apartments'].append(listing)
                new_count += 1
        
        save_tracker(tracker)
        
        socketio.emit('scrape_complete', {
            'message': f'Found {len(all_listings)} total, {new_count} new listings added',
            'total': len(all_listings),
            'new': new_count
        })
        
    except Exception as e:
        socketio.emit('status', {'message': f'Scraping error: {str(e)}'})
        if 'driver' in locals():
            driver.quit()

def send_bulk_inquiries(apt_ids):
    """Send inquiries via StreetEasy using browser automation"""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    
    tracker = load_tracker()
    selected_apts = [a for a in tracker['apartments'] if a['id'] in apt_ids]
    
    if not selected_apts:
        socketio.emit('status', {'message': 'No apartments selected'})
        return
    
    socketio.emit('status', {'message': f'Sending {len(selected_apts)} inquiries...'})
    
    options = Options()
    # NOT headless so user can see and complete CAPTCHA if needed
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.maximize_window()
        
        for apt in selected_apts:
            if not apt.get('url'):
                continue
                
            socketio.emit('status', {'message': f'Opening: {apt["address"]}'})
            
            try:
                driver.get(apt['url'])
                time.sleep(3)
                
                # Look for contact/inquiry button
                contact_btn = None
                for selector in [
                    "button[data-testid='contact-button']",
                    "button.contact-button",
                    "a[href*='contact']",
                    "button:contains('Contact')",
                    ".listing-agent-contact button"
                ]:
                    try:
                        contact_btn = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if contact_btn:
                    contact_btn.click()
                    time.sleep(2)
                    
                    # Fill in the inquiry form
                    message = generate_inquiry(apt['address'], apt.get('broker_name'))
                    
                    # Try to find and fill message field
                    for msg_selector in ['textarea[name="message"]', 'textarea', '#message', '.message-input']:
                        try:
                            msg_field = driver.find_element(By.CSS_SELECTOR, msg_selector)
                            msg_field.clear()
                            msg_field.send_keys(message)
                            socketio.emit('status', {'message': f'Message filled for {apt["address"]}'})
                            break
                        except:
                            continue
                    
                    # Fill name if field exists
                    for name_selector in ['input[name="name"]', '#name', 'input[placeholder*="name"]']:
                        try:
                            name_field = driver.find_element(By.CSS_SELECTOR, name_selector)
                            name_field.clear()
                            name_field.send_keys(PROFILE['name'])
                            break
                        except:
                            continue
                    
                    # Fill email if field exists
                    for email_selector in ['input[name="email"]', '#email', 'input[type="email"]']:
                        try:
                            email_field = driver.find_element(By.CSS_SELECTOR, email_selector)
                            email_field.clear()
                            email_field.send_keys(PROFILE['email'])
                            break
                        except:
                            continue
                    
                    socketio.emit('inquiry_ready', {
                        'apartment_id': apt['id'],
                        'address': apt['address'],
                        'message': 'Form filled - please review and submit manually'
                    })
                    
                    # Wait for user to review and submit
                    socketio.emit('status', {'message': f'Review and submit inquiry for {apt["address"]}. Waiting 30 seconds...'})
                    time.sleep(30)
                    
                    # Update status
                    apt['status'] = 'contacted'
                    apt['contacted_at'] = datetime.now().isoformat()
                    
                else:
                    socketio.emit('status', {'message': f'No contact button found for {apt["address"]}'})
                    
            except Exception as e:
                socketio.emit('status', {'message': f'Error with {apt["address"]}: {str(e)}'})
                continue
        
        save_tracker(tracker)
        driver.quit()
        
        socketio.emit('inquiries_complete', {
            'message': f'Processed {len(selected_apts)} inquiries',
            'count': len(selected_apts)
        })
        
    except Exception as e:
        socketio.emit('status', {'message': f'Browser error: {str(e)}'})
        if 'driver' in locals():
            driver.quit()

if __name__ == '__main__':
    print("🏠 Apartment Hunter starting on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
