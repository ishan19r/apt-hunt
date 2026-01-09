#!/usr/bin/env python3
"""
🏠 Apartment Hunter Pro v2.0
Professional NYC apartment hunting automation for Ishan
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import threading
import time
import random
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ishan-apt-hunter-2026-pro'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

CONFIG = {
    "profile": {
        "name": "Ishan",
        "email": "ishan.19r@gmail.com",
        "phone": "",
        "income": 110000,
        "max_rent_40x": 110000 // 40,
    },
    "search": {
        "min_rent": 2400,
        "max_rent": 3200,
        "bedrooms": 1,
        "neighborhoods": [
            {"id": "east-harlem", "name": "East Harlem", "enabled": True},
            {"id": "yorkville", "name": "Yorkville", "enabled": True},
            {"id": "upper-east-side", "name": "Upper East Side", "enabled": True},
            {"id": "harlem", "name": "Harlem", "enabled": True},
            {"id": "washington-heights", "name": "Washington Heights", "enabled": False},
            {"id": "inwood", "name": "Inwood", "enabled": False},
        ],
        "no_fee_only": False,
    },
    "budget": {
        "monthly_take_home": 5250,
        "utilities": 150,
        "groceries": 400,
        "transport": 132,
        "target_dining": 500,
        "target_savings": 300,
    },
    "scraping": {
        "delay_min": 2,
        "delay_max": 5,
        "max_listings_per_neighborhood": 15,
    }
}

TRACKER_FILE = "data/apartments.json"
LOG_FILE = "data/activity.log"

def ensure_data_dir():
    os.makedirs("data", exist_ok=True)

def load_tracker():
    ensure_data_dir()
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {"apartments": [], "inquiries_sent": [], "last_scrape": None}

def save_tracker(data):
    ensure_data_dir()
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def log_activity(message, level="info"):
    ensure_data_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level.upper()}] {message}\n"
    with open(LOG_FILE, 'a') as f:
        f.write(entry)
    print(entry.strip())

def calculate_score(apt):
    score = 0
    rent = apt.get("rent", 9999)
    max_rent = CONFIG["profile"]["max_rent_40x"]
    if rent <= max_rent:
        margin = (max_rent - rent) / max_rent
        score += 40 * (1 + margin)
    else:
        score += max(0, 20 - ((rent - max_rent) / 100))
    budget = calculate_budget(rent)
    if budget["savings"] >= CONFIG["budget"]["target_savings"]:
        score += 15
    if budget["dining_out"] >= CONFIG["budget"]["target_dining"]:
        score += 15
    price_range = CONFIG["search"]["max_rent"] - CONFIG["search"]["min_rent"]
    price_position = (CONFIG["search"]["max_rent"] - rent) / price_range if price_range > 0 else 0
    score += 20 * price_position
    if apt.get("no_fee"):
        score += 10
    return min(100, max(0, round(score)))

def calculate_budget(rent):
    take_home = CONFIG["budget"]["monthly_take_home"]
    fixed = CONFIG["budget"]["utilities"] + CONFIG["budget"]["groceries"] + CONFIG["budget"]["transport"]
    after_fixed = take_home - rent - fixed
    dining = min(CONFIG["budget"]["target_dining"], max(0, after_fixed * 0.5))
    savings = max(0, after_fixed - dining)
    return {
        "rent": rent,
        "utilities": CONFIG["budget"]["utilities"],
        "groceries": CONFIG["budget"]["groceries"],
        "transport": CONFIG["budget"]["transport"],
        "dining_out": round(dining),
        "savings": round(savings),
        "total_expenses": rent + fixed + round(dining),
        "surplus": round(after_fixed - dining - savings) if after_fixed > dining else 0
    }

def check_40x(rent):
    return CONFIG["profile"]["income"] >= rent * 40

def generate_inquiry(apt):
    broker = apt.get("broker_name", "")
    greeting = f"Hi {broker}," if broker else "Hi,"
    return f"""{greeting}

I'm interested in the 1-bedroom at {apt.get('address', 'this location')}. A few questions:

1. Is the unit still available for immediate move-in?
2. Are there any additional fees beyond rent (amenity fees, move-in fees, etc.)?
3. What are the income/credit requirements for approval?
4. Is there any flexibility on the lease terms?

I'd love to schedule a viewing at your earliest convenience. I'm available:
- Weekdays after 5:30pm
- Weekends anytime

Thank you!
{CONFIG['profile']['name']}
{CONFIG['profile']['email']}"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(CONFIG)

@app.route('/api/config', methods=['PUT'])
def update_config():
    global CONFIG
    data = request.json
    if "search" in data:
        CONFIG["search"].update(data["search"])
    if "profile" in data:
        CONFIG["profile"].update(data["profile"])
        CONFIG["profile"]["max_rent_40x"] = CONFIG["profile"]["income"] // 40
    return jsonify(CONFIG)

@app.route('/api/apartments', methods=['GET'])
def get_apartments():
    tracker = load_tracker()
    apartments = tracker.get("apartments", [])
    for apt in apartments:
        apt["score"] = calculate_score(apt)
        apt["budget"] = calculate_budget(apt.get("rent", 0))
        apt["passes_40x"] = check_40x(apt.get("rent", 0))
    apartments.sort(key=lambda x: x.get("score", 0), reverse=True)
    return jsonify({
        "apartments": apartments,
        "stats": {
            "total": len(apartments),
            "passing": len([a for a in apartments if a.get("passes_40x")]),
            "selected": len([a for a in apartments if a.get("selected")]),
            "contacted": len([a for a in apartments if a.get("status") == "contacted"]),
        },
        "last_scrape": tracker.get("last_scrape")
    })

@app.route('/api/apartments', methods=['POST'])
def add_apartment():
    data = request.json
    tracker = load_tracker()
    existing_urls = {a.get("url") for a in tracker["apartments"]}
    if data.get("url") in existing_urls:
        return jsonify({"error": "Apartment already exists"}), 400
    apt = {
        "id": str(int(time.time() * 1000)),
        "address": data.get("address", ""),
        "rent": int(data.get("rent", 0)),
        "neighborhood": data.get("neighborhood", ""),
        "url": data.get("url", ""),
        "image_url": data.get("image_url", ""),
        "broker_name": data.get("broker_name", ""),
        "broker_email": data.get("broker_email", ""),
        "broker_phone": data.get("broker_phone", ""),
        "no_fee": data.get("no_fee", False),
        "days_on_market": data.get("days_on_market"),
        "notes": data.get("notes", ""),
        "added_at": datetime.now().isoformat(),
        "status": "new",
        "selected": False,
    }
    tracker["apartments"].append(apt)
    save_tracker(tracker)
    log_activity(f"Added apartment: {apt['address']} - ${apt['rent']}/mo")
    return jsonify(apt)

@app.route('/api/apartments/<apt_id>', methods=['PUT'])
def update_apartment(apt_id):
    data = request.json
    tracker = load_tracker()
    for apt in tracker["apartments"]:
        if apt["id"] == apt_id:
            apt.update(data)
            save_tracker(tracker)
            return jsonify(apt)
    return jsonify({"error": "Not found"}), 404

@app.route('/api/apartments/<apt_id>', methods=['DELETE'])
def delete_apartment(apt_id):
    tracker = load_tracker()
    tracker["apartments"] = [a for a in tracker["apartments"] if a["id"] != apt_id]
    save_tracker(tracker)
    return jsonify({"success": True})

@app.route('/api/apartments/<apt_id>/select', methods=['POST'])
def toggle_select(apt_id):
    tracker = load_tracker()
    for apt in tracker["apartments"]:
        if apt["id"] == apt_id:
            apt["selected"] = not apt.get("selected", False)
            save_tracker(tracker)
            return jsonify(apt)
    return jsonify({"error": "Not found"}), 404

@app.route('/api/apartments/<apt_id>/inquiry', methods=['GET'])
def get_inquiry(apt_id):
    tracker = load_tracker()
    for apt in tracker["apartments"]:
        if apt["id"] == apt_id:
            return jsonify({"message": generate_inquiry(apt), "apartment": apt})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/export', methods=['GET'])
def export_csv():
    tracker = load_tracker()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Address", "Rent", "Neighborhood", "Score", "40x Pass", "Status", "URL", "Added"])
    for apt in tracker["apartments"]:
        writer.writerow([apt.get("address"), apt.get("rent"), apt.get("neighborhood"), calculate_score(apt), "Yes" if check_40x(apt.get("rent", 0)) else "No", apt.get("status"), apt.get("url"), apt.get("added_at", "")[:10]])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name=f'apartments_{datetime.now().strftime("%Y%m%d")}.csv')

@app.route('/api/clear-all', methods=['DELETE'])
def clear_all():
    save_tracker({"apartments": [], "inquiries_sent": [], "last_scrape": None})
    return jsonify({"success": True})

@socketio.on('connect')
def handle_connect():
    emit('status', {'type': 'success', 'message': 'Connected to Apartment Hunter Pro'})
    log_activity("Client connected")

@socketio.on('start_scrape')
def handle_scrape(data):
    emit('status', {'type': 'info', 'message': 'Initializing search...'})
    thread = threading.Thread(target=scrape_streeteasy, args=(data,))
    thread.daemon = True
    thread.start()

@socketio.on('send_inquiries')
def handle_send_inquiries(data):
    apt_ids = data.get('apartment_ids', [])
    if not apt_ids:
        emit('status', {'type': 'error', 'message': 'No apartments selected'})
        return
    emit('status', {'type': 'info', 'message': f'Preparing {len(apt_ids)} inquiries...'})
    thread = threading.Thread(target=send_inquiries_browser, args=(apt_ids,))
    thread.daemon = True
    thread.start()

def scrape_streeteasy(data):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
    import re
    socketio.emit('scrape_started', {})
    log_activity("Starting StreetEasy scrape")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36']
    options.add_argument(f'user-agent={random.choice(user_agents)}')
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        neighborhoods = data.get('neighborhoods', [n['id'] for n in CONFIG['search']['neighborhoods'] if n['enabled']])
        min_rent = data.get('min_rent', CONFIG['search']['min_rent'])
        max_rent = data.get('max_rent', CONFIG['search']['max_rent'])
        no_fee_only = data.get('no_fee_only', CONFIG['search']['no_fee_only'])
        all_listings = []
        tracker = load_tracker()
        existing_urls = {a.get('url') for a in tracker['apartments']}
        for i, neighborhood in enumerate(neighborhoods):
            progress = ((i + 1) / len(neighborhoods)) * 100
            socketio.emit('scrape_progress', {'neighborhood': neighborhood.replace('-', ' ').title(), 'progress': progress, 'found': len(all_listings)})
            url = f"https://streeteasy.com/for-rent/{neighborhood}/price:{min_rent}-{max_rent}%7Cbeds:1"
            if no_fee_only:
                url += "%7Cno_fee:1"
            socketio.emit('status', {'type': 'info', 'message': f'Searching {neighborhood.replace("-", " ").title()}...'})
            log_activity(f"Scraping: {url}")
            try:
                delay = random.uniform(CONFIG['scraping']['delay_min'], CONFIG['scraping']['delay_max'])
                time.sleep(delay)
                driver.get(url)
                time.sleep(3)
                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='listing-card'], .listingCard, .searchCardList")))
                except:
                    socketio.emit('status', {'type': 'warning', 'message': f'No listings found in {neighborhood}'})
                    continue
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                listings = soup.select('[data-testid="listing-card"]') or soup.select('.listingCard') or soup.select('article.listing') or soup.select('.searchCardList > div')
                socketio.emit('status', {'type': 'info', 'message': f'Found {len(listings)} listings in {neighborhood.replace("-", " ").title()}'})
                for listing in listings[:CONFIG['scraping']['max_listings_per_neighborhood']]:
                    try:
                        address_elem = listing.select_one('address') or listing.select_one('[data-testid="listing-address"]') or listing.select_one('.listingCard-address') or listing.select_one('h3')
                        address = address_elem.get_text(strip=True) if address_elem else "Unknown Address"
                        price_elem = listing.select_one('[data-testid="price"]') or listing.select_one('.price') or listing.select_one('[class*="price"]')
                        price_text = price_elem.get_text(strip=True) if price_elem else "0"
                        rent = int(re.sub(r'[^\d]', '', price_text) or 0)
                        link_elem = listing.select_one('a[href*="/rental/"]')
                        listing_url = ""
                        if link_elem and link_elem.get('href'):
                            href = link_elem['href']
                            listing_url = href if href.startswith('http') else f"https://streeteasy.com{href}"
                        img_elem = listing.select_one('img')
                        image_url = img_elem.get('src', '') if img_elem else ""
                        no_fee = bool(listing.select_one('[class*="no-fee"], [class*="noFee"], .noFee'))
                        if rent < min_rent or rent > max_rent:
                            continue
                        if listing_url in existing_urls:
                            continue
                        apt_data = {"id": str(int(time.time() * 1000) + random.randint(1, 999)), "address": address, "rent": rent, "neighborhood": neighborhood.replace('-', ' ').title(), "url": listing_url, "image_url": image_url, "no_fee": no_fee, "broker_name": "", "notes": "", "added_at": datetime.now().isoformat(), "status": "new", "selected": False}
                        all_listings.append(apt_data)
                        existing_urls.add(listing_url)
                        socketio.emit('listing_found', {'apartment': apt_data, 'score': calculate_score(apt_data), 'passes_40x': check_40x(rent)})
                    except Exception as e:
                        log_activity(f"Error parsing listing: {str(e)}", "error")
                        continue
            except Exception as e:
                socketio.emit('status', {'type': 'error', 'message': f'Error in {neighborhood}: {str(e)}'})
                log_activity(f"Scrape error in {neighborhood}: {str(e)}", "error")
                continue
        driver.quit()
        tracker = load_tracker()
        tracker['apartments'].extend(all_listings)
        tracker['last_scrape'] = datetime.now().isoformat()
        save_tracker(tracker)
        socketio.emit('scrape_complete', {'total_found': len(all_listings), 'passing_40x': len([a for a in all_listings if check_40x(a['rent'])]), 'message': f'Found {len(all_listings)} new apartments!'})
        log_activity(f"Scrape complete: {len(all_listings)} new apartments")
    except Exception as e:
        socketio.emit('status', {'type': 'error', 'message': f'Scraping failed: {str(e)}'})
        log_activity(f"Scrape failed: {str(e)}", "error")
        if 'driver' in locals():
            driver.quit()

def send_inquiries_browser(apt_ids):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    tracker = load_tracker()
    selected = [a for a in tracker['apartments'] if a['id'] in apt_ids]
    if not selected:
        socketio.emit('status', {'type': 'error', 'message': 'No apartments found'})
        return
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        for i, apt in enumerate(selected):
            socketio.emit('inquiry_progress', {'current': i + 1, 'total': len(selected), 'apartment': apt['address']})
            if not apt.get('url'):
                continue
            try:
                driver.get(apt['url'])
                time.sleep(3)
                contact_selectors = ["button[data-testid='contact-button']", "button[class*='contact']", "a[class*='contact']", ".listing-agent button"]
                clicked = False
                for selector in contact_selectors:
                    try:
                        btn = driver.find_element(By.CSS_SELECTOR, selector)
                        btn.click()
                        clicked = True
                        time.sleep(2)
                        break
                    except:
                        continue
                if clicked:
                    message = generate_inquiry(apt)
                    field_mappings = [(['textarea[name="message"]', 'textarea', '#message'], message), (['input[name="name"]', '#name'], CONFIG['profile']['name']), (['input[name="email"]', 'input[type="email"]', '#email'], CONFIG['profile']['email']), (['input[name="phone"]', 'input[type="tel"]', '#phone'], CONFIG['profile']['phone'])]
                    for selectors, value in field_mappings:
                        if not value:
                            continue
                        for selector in selectors:
                            try:
                                field = driver.find_element(By.CSS_SELECTOR, selector)
                                field.clear()
                                field.send_keys(value)
                                break
                            except:
                                continue
                    socketio.emit('inquiry_ready', {'apartment_id': apt['id'], 'address': apt['address'], 'message': 'Form filled! Review and click Submit.'})
                    socketio.emit('status', {'type': 'warning', 'message': f'Review form for {apt["address"]} - You have 45 seconds to submit'})
                    time.sleep(45)
                    apt['status'] = 'contacted'
                    apt['contacted_at'] = datetime.now().isoformat()
                else:
                    socketio.emit('status', {'type': 'warning', 'message': f'No contact button found for {apt["address"]}'})
            except Exception as e:
                socketio.emit('status', {'type': 'error', 'message': f'Error: {str(e)}'})
                continue
        save_tracker(tracker)
        driver.quit()
        socketio.emit('inquiries_complete', {'count': len(selected), 'message': f'Processed {len(selected)} inquiries!'})
    except Exception as e:
        socketio.emit('status', {'type': 'error', 'message': f'Browser error: {str(e)}'})
        if 'driver' in locals():
            driver.quit()

if __name__ == '__main__':
    ensure_data_dir()
    print("\n" + "="*60)
    print("🏠 APARTMENT HUNTER PRO v2.0")
    print("="*60)
    print(f"📍 Open: http://localhost:5000")
    print(f"💰 Your max rent (40x): ${CONFIG['profile']['max_rent_40x']:,}/mo")
    print(f"🔍 Search range: ${CONFIG['search']['min_rent']:,} - ${CONFIG['search']['max_rent']:,}")
    print("="*60 + "\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
