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
