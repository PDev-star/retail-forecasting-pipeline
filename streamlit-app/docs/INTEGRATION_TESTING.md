# Streamlit Integration Testing Guide

## Overview

This project uses **Streamlit AppTest** for integration testing UI components while maintaining fast unit tests for business logic. This guide explains the testing architecture, the "smart guard" pattern, and how to write new tests.

**Current Status:** ✅ **96.07% code coverage achieved** (Target: ≥80% for RFP S2-D-02)

## Architecture

### Testing Strategy

**Two-Tier Testing:**
1. **Unit Tests** - Fast, isolated tests for business logic (services/, utils/)
   * 30 tests covering API client, config, inventory, app module
   * Execution time: ~1 second
2. **Integration Tests** - Full UI flow tests using Streamlit AppTest
   * 16 tests covering complete user workflows
   * Execution time: ~20 seconds

**Total: 46 tests, all passing ✅**

### The Smart Guard Pattern

**Problem:** Unit tests and integration tests have conflicting needs:
- **Unit tests** need UI code BLOCKED (fast imports, no Streamlit rendering)
- **Integration tests** need UI code ENABLED (AppTest requires real UI)

**Solution:** Context-aware guard function using `APPTEST_MODE` environment variable

#### Implementation (app.py)

```python
def _should_run_ui() -> bool:
    """
    Determine if UI code should execute.
    
    Returns True when:
      - APPTEST_MODE=1 (integration tests need UI)
      - OR pytest not in sys.modules (normal Streamlit app)
    
    Returns False when:
      - pytest in sys.modules AND no APPTEST_MODE (unit tests)
    """
    # Integration tests explicitly set APPTEST_MODE
    if os.environ.get('APPTEST_MODE') == '1':
        return True
    
    # Unit tests have pytest in modules but no APPTEST_MODE
    if 'pytest' in sys.modules or 'PYTEST_CURRENT_TEST' in os.environ:
        return False
    
    # Normal Streamlit app execution
    return True

# All UI code wrapped in guard
if _should_run_ui():
    # Streamlit imports and rendering
    ...
```

See complete implementation in `app.py` lines 43-98.

#### Execution Contexts

| Context | pytest in sys.modules? | APPTEST_MODE? | UI Runs? | Use Case |
|---------|----------------------|--------------|----------|----------|
| **Normal App** | ❌ No | Not set | ✅ Yes | Production, development |
| **Unit Tests** | ✅ Yes | ❌ Not set | ❌ No | Fast business logic tests |
| **Integration Tests** | ✅ Yes | ✅ Set to '1' | ✅ Yes | Full UI workflow tests |

### Benefits

✅ Unit tests stay fast (~1 second)  
✅ Integration tests work (AppTest can render UI)  
✅ No code duplication  
✅ Simple to maintain  
✅ 96.07% coverage achieved

## Quick Start

### 1. Write an Integration Test

```python
# tests/test_ui_example.py
import os
import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def enable_apptest_mode():
    """Enable UI for integration tests"""
    os.environ['APPTEST_MODE'] = '1'
    yield
    os.environ.pop('APPTEST_MODE', None)

def test_forecast_button_click():
    """Test user clicks forecast button"""
    # Load app
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Mock API
    with patch('services.api_client.requests.post') as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = {
            "success": True,
            "forecast": {"values": [45, 46, 47]}
        }
        
        # Click button
        at.button[0].click().run()
        
        # Verify
        assert "forecast" in at.session_state
        assert len(at.success) > 0
```

### 2. Run the Test

```bash
cd streamlit-app
pytest tests/test_ui_example.py -v
```

## AppTest API

### Load App

```python
at = AppTest.from_file("../app.py")
at.run()
```

### Find Widgets

```python
# Find button by text
for btn in at.button:
    if "Generate Forecast" in str(btn):
        forecast_btn = btn

# Find slider by label
for slider in at.slider:
    if "Horizon" in str(slider.label):
        horizon_slider = slider

# Find selectbox
for selectbox in at.selectbox:
    if "Product" in str(selectbox.label):
        product_selector = selectbox
```

### Simulate Actions

```python
button.click().run()
slider.set_value(30).run()
selectbox.set_value("Option").run()
number_input.set_value(21).run()
```

### Check State

```python
# Session state
assert "forecast" in at.session_state
assert at.session_state["forecast"] == [10, 20, 30]

# Messages
assert len(at.success) > 0  # Success messages
assert len(at.error) > 0    # Error messages
assert len(at.info) > 0     # Info messages

# Verify no exceptions
assert len(at.exception) == 0
```

## Common Patterns

### Mock API Calls

```python
with patch('services.api_client.requests.post') as mock:
    mock.return_value.status_code = 200
    mock.return_value.json.return_value = {
        "success": True,
        "forecast": {"values": [10, 20, 30]}
    }
    
    # ... user interaction ...
    
    assert mock.called
    call_args = mock.call_args
    assert call_args[1]["params"]["horizon"] == 30
```

### Test Error Handling

```python
with patch('services.api_client.requests.post') as mock:
    import requests
    mock.side_effect = requests.exceptions.ConnectionError()
    
    button.click().run()
    
    assert len(at.error) > 0
    assert "Cannot connect" in at.error[0].value
```

### Test Different Scenarios

```python
# Select scenario
for selectbox in at.selectbox:
    if "Scenario" in str(selectbox.label):
        selectbox.set_value("Promotion (+30%)").run()
        break

# Generate forecast
at.button[0].click().run()

# Verify adjustment applied (1.3x multiplier)
forecast = at.session_state["forecast"]
assert forecast[0] == 13.0  # 10 * 1.3
```

## Coverage Configuration

The `.coveragerc` file excludes test mock code from coverage metrics:

```ini
[report]
exclude_lines =
    # Test environment import mocks
    except ImportError:
    class MockSidebar:
    class MockStreamlit:
    @staticmethod
```

This ensures coverage focuses on **production code** rather than test infrastructure.

**Result:** 96.07% coverage (229 statements, 9 missed)

## Best Practices

**DO** ✅
* Always set APPTEST_MODE=1 via fixture with `autouse=True`
* Mock all external API calls
* Test complete user flows (not individual functions)
* Verify both success and error paths
* Test all scenario types and parameter variations
* Check session state persistence

**DON'T** ❌
* Don't test Streamlit internals
* Don't write integration tests for pure logic (use unit tests)
* Don't forget to mock APIs (tests will hang)
* Don't test styling or exact UI layout
* Don't use `time.sleep()` (use `.run()` instead)

## Troubleshooting

### "StreamlitSecretNotFoundError"

Create `.streamlit/secrets.toml`:

```toml
fastapi_url = "http://localhost:8000"
api_key = "test-key"
```

### "Button not found"

Verify `APPTEST_MODE=1` fixture exists with `autouse=True`:

```python
@pytest.fixture(autouse=True)
def enable_apptest_mode():
    os.environ['APPTEST_MODE'] = '1'
    yield
    os.environ.pop('APPTEST_MODE', None)
```

### Tests hang

1. Check all APIs are mocked (unmocked APIs cause hangs)
2. Increase timeout: `AppTest.from_file("../app.py", default_timeout=60)`
3. Check for infinite loops in app logic

### "ModuleNotFoundError: streamlit.testing"

Install streamlit: `pip install streamlit`

(Required for integration tests, not for unit tests)

## Running Tests

```bash
# All tests with coverage
pytest --cov=. --cov-report=term-missing

# Only unit tests (fast, ~1 second)
pytest tests/test_api_client.py tests/test_app.py tests/test_config.py tests/test_inventory.py

# Only integration tests (~20 seconds)
pytest tests/test_ui_integration.py -v

# With verbose output
pytest -v

# With coverage report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Files

* **`tests/test_ui_integration.py`** - 16 integration tests covering full UI workflows
* **`tests/test_api_client.py`** - 13 unit tests for API client
* **`tests/test_config.py`** - 11 unit tests for configuration
* **`tests/test_inventory.py`** - 4 unit tests for inventory calculations
* **`tests/test_app.py`** - 2 unit tests for app module

## Resources

* **Integration Tests:** `tests/test_ui_integration.py` - Complete production test suite
* **Streamlit Docs:** https://docs.streamlit.io/develop/api-reference/app-testing
* **pytest Docs:** https://docs.pytest.org/
* **Coverage Report:** Run `pytest --cov=. --cov-report=html` and open `htmlcov/index.html`

---

**RFP S2-D-02 Status:** ✅ **Complete** - 96.07% coverage achieved (target: ≥80%)
