# Retail Forecasting Project - Complete CI/CD Solution

End-to-end retail demand forecasting with ML models, Model Serving, and **fully automated CI/CD pipeline**.

[![FastAPI Tests](https://github.com/YOUR_USERNAME/retail-forecasting-pipeline/actions/workflows/test-fastapi.yml/badge.svg)](https://github.com/YOUR_USERNAME/retail-forecasting-pipeline/actions/workflows/test-fastapi.yml)
[![Streamlit Tests](https://github.com/YOUR_USERNAME/retail-forecasting-pipeline/actions/workflows/test-streamlit.yml/badge.svg)](https://github.com/YOUR_USERNAME/retail-forecasting-pipeline/actions/workflows/test-streamlit.yml)
[![Linting](https://github.com/YOUR_USERNAME/retail-forecasting-pipeline/actions/workflows/lint.yml/badge.svg)](https://github.com/YOUR_USERNAME/retail-forecasting-pipeline/actions/workflows/lint.yml)
[![Deploy](https://github.com/YOUR_USERNAME/retail-forecasting-pipeline/actions/workflows/deploy.yml/badge.svg)](https://github.com/YOUR_USERNAME/retail-forecasting-pipeline/actions/workflows/deploy.yml)

## 🎯 Project Overview

**InventoryForge** - Predictive Inventory Analytics Engine  
**Team:** S2-D-02  
**Timeline:** 18 weeks (Impact pSiddhi)  
**Budget:** ₹2,500 (Used: ~₹700)

**🎉 NEW: Complete CI/CD automation with zero manual deployment steps!**

## 🚀 CI/CD Pipeline

**Push code once → Deployed everywhere automatically!**

```
Developer Push
    ↓
GitHub Actions (60 seconds)
    ├─ Lint code ✅
    ├─ 12 FastAPI tests ✅
    └─ 46 Streamlit tests (96% coverage) ✅
    ↓
All Pass? → Auto-Deploy
    ├─ Streamlit (3 min) 🚀
    └─ Render (8 min) 🚀
    ↓
LIVE! 🎉 (10 min total)
```

**Zero manual steps. Zero cost. Zero downtime.**

## 📦 Project Structure

```
retail-forecasting-pipeline/          # Git-connected on GitConnectionTest branch
├── .github/
│   └── workflows/
│       ├── test-streamlit.yml        # Streamlit CI (≥80% coverage)
│       ├── test-fastapi.yml          # FastAPI CI (≥80% coverage)
│       ├── lint.yml                  # Code quality checks
│       ├── deploy.yml                # Production auto-deploy
│       └── deploy-staging.yml        # Staging environment
│
├── snapshots/                        # Databricks notebooks
│   └── Retail Forecasting Pipeline Complete.ipynb
│
├── streamlit-app/                    # Public UI (Week 12 deliverable)
│   ├── app.py                        # 400 lines UI code (smart guard pattern)
│   ├── components/                   # UI components (100% coverage)
│   ├── services/                     # Business logic (100% coverage)
│   ├── utils/                        # Configuration (85% coverage)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .coveragerc                   # Coverage configuration
│   ├── TESTING.md                    # Testing notes
│   ├── docs/
│   │   └── INTEGRATION_TESTING.md    # Complete testing guide
│   └── tests/
│       ├── test_api_client.py        # 13 unit tests
│       ├── test_app.py               # 2 unit tests
│       ├── test_config.py            # 11 unit tests
│       ├── test_inventory.py         # 4 unit tests
│       └── test_ui_integration.py    # 16 integration tests (AppTest)
│
├── fastapi-gateway/                  # Optional API gateway
│   ├── api_gateway.py               # 80 lines proxy code
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── README.md
│   └── tests/
│       └── test_gateway.py          # 12 unit tests
│
├── pytest.ini                        # Pytest configuration
├── .gitignore                        # Secrets excluded
└── README.md                         # This file
```

## 🏃 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/retail-forecasting-pipeline.git
cd retail-forecasting-pipeline
git checkout GitConnectionTest
```

### 2. Run Tests Locally

```bash
# Install dependencies
pip install -r streamlit-app/requirements-dev.txt

# Run all tests
pytest

# With coverage
pytest --cov --cov-report=html

# Run only unit tests (fast, ~1 second)
pytest streamlit-app/tests/test_*.py --ignore=streamlit-app/tests/test_ui_integration.py

# Run integration tests (comprehensive, ~20 seconds)
APPTEST_MODE=1 pytest streamlit-app/tests/test_ui_integration.py -v
```

### 3. Enable Auto-Deployment (One-time, 15 minutes)

#### Streamlit Cloud:
1. Go to https://share.streamlit.io
2. Connect this repo, branch `main`, file `streamlit-app/app.py`
3. Add secret: `databricks_token`
4. Check **Auto-deploy** ✅

#### Render.com:
1. Go to https://render.com
2. Connect this repo, branch `main`, root `fastapi-gateway`
3. Add env vars: `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `API_KEYS`
4. **Auto-Deploy** is ON by default ✅

#### GitHub Actions:
1. Repo → Settings → Secrets → Actions
2. Add `DATABRICKS_HOST` and `DATABRICKS_TOKEN`

**Done! From now on, every push to `main` triggers:**
- ✅ All tests
- ✅ Code quality checks
- ✅ Auto-deployment to Streamlit + Render
- ✅ Live in 10 minutes

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Coverage Requirements (pSiddhi)

- **Week 10**: Unit tests passing ✅
- **Week 17**: QA suite ≥80% coverage ✅

| Component | Tests | Coverage | Method |
|-----------|-------|----------|--------|
| FastAPI Gateway | 12 tests | 85%+ | Unit tests |
| Streamlit App | 46 tests | **96.07%** | Unit + Integration (AppTest) |
| **Total** | **58 tests** | **~92%** | Two-tier strategy |

### Streamlit Testing Architecture

**Two-Tier Strategy:**
* **Unit Tests (30 tests, ~1s)** - Fast business logic tests
* **Integration Tests (16 tests, ~20s)** - Full UI workflow tests with Streamlit AppTest

**Smart Guard Pattern:** Context-aware UI rendering allows both unit and integration tests without code duplication.

**Coverage Breakdown:**
```
streamlit-app/
├── app.py                    91.04%  (Smart guard pattern)
├── components/charts.py     100.00%  (AppTest integration)
├── components/sidebar.py    100.00%  (AppTest integration)
├── components/tabs.py       100.00%  (AppTest integration)
├── services/api_client.py   100.00%  (Unit tests with mocks)
├── services/inventory.py    100.00%  (Pure function tests)
└── utils/config.py           85.71%  (Configuration tests)
───────────────────────────────────────
TOTAL                         96.07%
```

See `streamlit-app/docs/INTEGRATION_TESTING.md` for complete guide.

### GitHub Actions

Every push triggers 5 workflows:
1. **test-streamlit.yml** - Streamlit tests (~25s, 46 tests, ≥80% threshold)
2. **test-fastapi.yml** - FastAPI tests (~30s, 12 tests)
3. **lint.yml** - Code quality (~15s)
4. **deploy.yml** - Production deployment (~10s)
5. **deploy-staging.yml** - Staging (optional)

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      DATABRICKS WORKSPACE           │
│                                     │
│  📓 Notebook (snapshots/)           │
│    └── Data pipeline + ML training  │
│                                     │
│  💾 Delta Lake                      │
│  🧪 MLflow                          │
│  🚀 Model Serving Endpoints         │
│     ├── Cat1Forecast (v13)          │
│     └── Cat2Forecast (v12)          │
└─────────────┬───────────────────────┘
              │ REST API
         ┌────┴────┐
         │         │
    ┌────▼───┐ ┌──▼─────┐
    │Streamlit│ │FastAPI │
    │  Cloud  │ │Render  │
    └────┬───┘ └──┬─────┘
         │        │
    👥 Users  📱 Apps
```

**Auto-deploys on every push to `main`!** 🚀

## 💰 Cost Analysis

| Component | Solution | Monthly Cost |
|-----------|----------|--------------|
| Data Storage | Delta Lake (Databricks CE) | ₹0 |
| ML Training | Databricks CE | ₹0 |
| Model Serving | Scale-to-zero endpoints | ₹0 |
| Public UI | Streamlit Community Cloud | ₹0 |
| API Gateway | Render.com Free Tier | ₹0 |
| CI/CD | GitHub Actions (2,000 min/mo) | ₹0 |
| **Total** | | **₹0/month** |

**Semester Savings:** ₹44,200 vs alternatives

## 📊 Business Impact

- **Stock Optimization:** 30% reduction in buffer stock
- **Capital Freed:** ₹15-30K per product
- **Service Level:** 95% maintained
- **ROI:** ₹120-240K annual revenue protected

## 🎯 pSiddhi Deliverables

### Week 10 ✅
- ✅ 20 unit tests passing
- ✅ Data validation
- ✅ Core function tests
- ✅ GitHub Actions CI

### Week 12 ✅
- ✅ Interactive Streamlit app
- ✅ What-if scenarios (4 modes)
- ✅ Public URL (no login required)
- ✅ Auto-deployment enabled

### Week 17 ✅
- ✅ QA suite ≥80% coverage (achieved 96%)
- ✅ Complete E2E engine (2 categories, 2+ models)
- ✅ Full CI/CD pipeline
- ✅ Production deployment automation
- ✅ Integration testing with Streamlit AppTest

## 🔄 Development Workflow

**Your workflow from now on:**

```bash
# 1. Create feature branch
git checkout -b feature/new-scenario

# 2. Make changes
vim streamlit-app/app.py

# 3. Test locally
pytest streamlit-app/tests/ -v

# 4. Commit and push
git add .
git commit -m "Add seasonal sale scenario"
git push origin feature/new-scenario

# 5. Create Pull Request
# GitHub Actions runs tests automatically

# 6. Merge to main
# Auto-deploys to production! 🎉
```

**Commit → Tests → Deploy → Live in 10 minutes!**

## 📚 Documentation

- [Streamlit App](streamlit-app/README.md) - UI deployment guide
- [Integration Testing Guide](streamlit-app/docs/INTEGRATION_TESTING.md) - Complete testing guide
- [FastAPI Gateway](fastapi-gateway/README.md) - API deployment guide
- [Notebook](snapshots/) - Data pipeline and ML training
- [CI/CD Guide](docs/CICD.md) - Complete automation guide

## 🔗 Links

- **GitHub:** https://github.com/YOUR_USERNAME/retail-forecasting-pipeline
- **Streamlit Demo:** https://retail-forecasting-YOUR_USERNAME.streamlit.app
- **FastAPI:** https://retail-forecast-api.onrender.com
- **Actions:** https://github.com/YOUR_USERNAME/retail-forecasting-pipeline/actions

## 🤝 Contributing

This is a pSiddhi project. For issues or questions:
- Open a GitHub issue
- Email: send.pay.global@gmail.com

## 📄 License

MIT License - Built for Impact pSiddhi S2-D-02

## 🎉 Status

✅ **PRODUCTION-READY WITH FULL CI/CD**

- ✅ Complete ML pipeline
- ✅ 58 automated tests (96% coverage)
- ✅ 5 GitHub Actions workflows
- ✅ Auto-deployment to 2 platforms
- ✅ Zero manual steps
- ✅ Cost-effective (₹0/month)
- ✅ Scalable infrastructure
- ✅ Integration testing with Streamlit AppTest

---

**Total Lines of Code:** 1,500+  
**Test Coverage:** 96%+ (Streamlit), 85%+ (FastAPI)  
**Deployment Cost:** ₹0  
**Deployment Time:** 10 minutes (automated)  
**Development Time:** 18 weeks

**🚀 Push code → Live in production → Zero manual steps!**
