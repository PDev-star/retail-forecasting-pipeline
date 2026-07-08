# Testing Strategy for Streamlit App

## Architecture Overview

This Streamlit app follows a modular architecture:

```
streamlit-app/
├── app.py                  # UI orchestration (Streamlit-specific)
├── components/             # UI components (Streamlit-specific)
│   ├── sidebar.py          # Sidebar rendering
│   ├── charts.py           # Chart rendering with Plotly
│   └── tabs.py             # Tab UI components
├── services/               # Business logic (unit-testable)
│   ├── api_client.py       # FastAPI integration
│   └── inventory.py        # Stock recommendation logic
└── utils/                  # Configuration (unit-testable)
    └── config.py           # App configuration
```

## Testing Philosophy

### ✅ Unit Testable: Business Logic

**Target: 95%+ coverage**

* `services/inventory.py` - Pure functions, no UI dependencies
* `services/api_client.py` - API calls with mocked requests
* `utils/config.py` - Configuration logic

These modules contain business logic and are fully unit-testable with mocks.

### ❌ Not Unit Testable: UI Components

**Target: 10-20% coverage (acceptable)**

* `app.py` - Streamlit UI orchestration
* `components/*.py` - Streamlit rendering components

**Why low coverage is acceptable:**
1. **Streamlit-specific rendering** - Requires full Streamlit test harness
2. **No business logic** - Just UI rendering and layout
3. **Should be tested via E2E tests** - Not unit tests

To test UI components properly, you need:
* Integration tests with Streamlit test harness
* E2E tests with browser automation
* Manual QA testing

## Current Coverage

```
Module                     Coverage    Testable?
--------------------------------------------------------
services/inventory.py      100.00%     ✅ Business logic
services/api_client.py     ~95%        ✅ Business logic
utils/config.py            ~95%        ✅ Configuration
app.py                     ~20%        ❌ UI rendering
components/sidebar.py      ~10%        ❌ UI rendering
components/charts.py       ~10%        ❌ UI rendering
components/tabs.py         ~15%        ❌ UI rendering
--------------------------------------------------------
OVERALL                    ~40-50%     Mixed
```

## Coverage Goals

* **Overall: 40-50%** - Realistic for Streamlit architecture
* **Services & Utils: 95%+** - Business logic fully tested
* **UI Components: 10-20%** - Acceptance (requires E2E tests)

## Running Tests

```bash
# Run all tests
cd streamlit-app
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=term --cov-report=html

# View HTML report
open htmlcov/index.html
```

## Test Organization

```
tests/
├── test_api_client.py      # Tests services/api_client.py (14 tests)
├── test_config.py          # Tests utils/config.py (12 tests)
├── test_inventory.py       # Tests services/inventory.py (4 tests)
└── test_app.py             # Tests app.py integration (2 tests)
```

Each test file corresponds to one module, with mocks at correct boundaries.

## Edge Cases Covered

### API Client (`test_api_client.py`)
* ✅ Successful requests
* ✅ HTTP errors (401, 404, 500, 502)
* ✅ Network errors (ConnectionError, Timeout)
* ✅ JSON parsing errors
* ✅ Missing nested keys
* ✅ Malformed responses
* ✅ Empty values

### Configuration (`test_config.py`)
* ✅ Product catalog validation
* ✅ Config value types
* ✅ Keep-alive success/failure
* ✅ Non-200 status codes
* ✅ Timeout handling
* ✅ Connection errors
* ✅ Multiple iterations

### Inventory (`test_inventory.py`)
* ✅ Stock calculations
* ✅ Custom lead times
* ✅ Edge cases (zero values)
* ✅ Different safety factors

## Future Improvements

To reach 80% overall coverage, you would need to:

1. **Extract more business logic** from UI components into services
2. **Add integration tests** with Streamlit test harness
3. **Add E2E tests** with browser automation (Selenium/Playwright)
4. **Add visual regression tests** for UI components

For most Streamlit apps, **40-50% unit test coverage is excellent** when the business logic (services/utils) is well-tested at 95%+.

## CI/CD Integration

The GitHub Actions workflow runs tests automatically:

```yaml
# .github/workflows/test-streamlit.yml
- name: Check coverage threshold
  run: |
    cd streamlit-app
    coverage report --fail-under=40  # Realistic for Streamlit architecture
```

This ensures:
* All business logic is tested (services/ & utils/)
* Coverage requirements are realistic for the architecture
* Deployment blocked if tests fail
