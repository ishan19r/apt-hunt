# 🏠 Apartment Hunter

Automated apartment hunting tools for NYC apartment search.

## Criteria
- **Budget:** $2,400 - $3,200/month
- **Target:** $2,600 (passes 40x, best lifestyle balance)
- **Areas:** East Harlem, Yorkville, UES
- **Income:** $110,000 (max rent @ 40x = $2,750)

## Files
- `apartment_hunter.py` - Budget analysis & search helper
- `apartment_tracker.py` - Track listings & generate responses
- `tracked_apartments.json` - Saved listings data

## Usage
```bash
python apartment_hunter.py   # Budget scenarios
python apartment_tracker.py  # View tracked apartments
```

## Current Top Pick
**Doron's 3rd floor unit @ $2,700** - Try to negotiate to $2,600

## Testing

Run all tests:
```bash
python run_tests.py
```

Run specific test suites:
```bash
python -m pytest tests/test_unit.py        # Unit tests
python -m pytest tests/test_integration.py  # Integration tests
python -m pytest tests/test_e2e.py          # End-to-end tests
```

### Test Coverage
- **Unit Tests**: Affordability calculations, budget math, criteria validation
- **Integration Tests**: File I/O, tracker persistence, response generation
- **E2E Tests**: Full workflows (search → track → inquire → negotiate)

## 🌐 Web App (Browser Automation)

### Quick Start
```bash
# Windows
run.bat

# Mac/Linux
./run.sh
```

Then open **http://localhost:5000**

### Features
- **🔍 Auto-Search**: Scrapes StreetEasy listings matching your criteria
- **✅ Smart Filtering**: Shows 40x income rule pass/fail for each listing
- **📊 Budget Impact**: See dining out & savings for each rent level
- **☑️ Select & Send**: Check apartments you like, send bulk inquiries
- **📧 Auto-Fill**: Browser fills inquiry forms automatically
- **🔗 Direct Links**: Click to view any listing on StreetEasy

### How It Works
1. Set your rent range and neighborhoods
2. Click "Search StreetEasy" - bot scrapes listings
3. Review results, check boxes for ones you like
4. Click "Send Selected Inquiries" - browser opens and fills forms
5. Review each form and click submit (handles CAPTCHAs manually)

### Tech Stack
- Flask + Flask-SocketIO (real-time updates)
- Selenium (browser automation)
- BeautifulSoup (HTML parsing)
- WebDriver Manager (auto Chrome driver)
