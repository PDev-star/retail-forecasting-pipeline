#!/bin/bash
# Local test runner for AI Insights
# Run this before pushing to verify coverage is maintained

set -e  # Exit on error

echo "========================================"
echo "  AI Insights Test Runner"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Must run from streamlit-app/ directory"
    echo "   cd streamlit-app && ./run_tests_local.sh"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
pip install -q -r requirements-dev.txt
echo "✅ Dependencies installed"
echo ""

# Run AI insights tests only (fast)
echo "========================================"
echo "  Running AI Insights Tests (33 tests)"
echo "========================================"
echo ""
pytest tests/test_ai_insights.py tests/test_ai_insights_integration.py -v --tb=short
echo ""

# Run full test suite with coverage
echo "========================================"
echo "  Running Full Test Suite with Coverage"
echo "========================================"
echo ""

# Unit tests
export PYTHONPATH=.
pytest tests/test_api_client.py \
       tests/test_app.py \
       tests/test_config.py \
       tests/test_inventory.py \
       tests/test_ai_insights.py \
       tests/test_ai_insights_integration.py \
  --cov=. --cov-report= -v --tb=short

# Integration tests
export APPTEST_MODE=1
pytest tests/test_ui_integration.py \
  --cov=. --cov-append --cov-report=term --cov-report=html -v --tb=short

echo ""
echo "========================================"
echo "  Coverage Report"
echo "========================================"
echo ""

# Check coverage threshold
coverage report

echo ""
echo "📊 HTML coverage report: htmlcov/index.html"
echo ""

# Check if coverage meets threshold
if coverage report --fail-under=80 > /dev/null 2>&1; then
    echo "✅ Coverage threshold met (80%+)"
    echo ""
    echo "========================================"
    echo "  ✅ ALL TESTS PASSED!"
    echo "========================================"
    echo ""
    echo "Safe to push! 🚀"
    echo ""
    exit 0
else
    echo "❌ Coverage below 80% threshold"
    echo "   Run: open htmlcov/index.html"
    echo "   to see which lines are not covered"
    echo ""
    exit 1
fi
