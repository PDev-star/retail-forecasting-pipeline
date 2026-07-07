# CI/CD Architecture - CORRECT IMPLEMENTATION

## The Right Way: Test BEFORE Deploy

```
┌─────────────────────────────────────────────────────────┐
│  Push to main branch                                    │
└──────────────────┬──────────────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       │                       │
       v                       v
┌──────────────────┐    ┌──────────────────┐
│ test-streamlit   │    │ test-fastapi     │
│ ================ │    │ ================ │
│ 1. Unit tests    │    │ 1. Unit tests    │
│                  │    │ 2. Deploy to DEV │
│                  │    │ 3. Integration   │
│                  │    │    tests         │
└─────────┬────────┘    └─────────┬────────┘
          │                       │
          └───────────┬───────────┘
                      │
                      v (all tests passed)
            ┌─────────────────────┐
            │ deploy.yml          │
            │ ===============     │
            │ 1. Deploy FastAPI   │
            │    to PRODUCTION    │
            └─────────────────────┘
                      │
                      v
            ┌─────────────────────┐
            │ Streamlit           │
            │ auto-deploys ✨      │
            └─────────────────────┘
```

---

## Workflow Files

### 1. `test-streamlit.yml` (Testing Workflow)
**Triggers:** On push to main/develop/GitConnectionTest, PRs to main

**What it does:**
* ✅ Runs Streamlit unit tests
* ✅ Checks code coverage

**Does NOT deploy anything**

---

### 2. `test-fastapi.yml` (Testing + Integration Workflow)
**Triggers:** On push to main/develop/GitConnectionTest, PRs to main

**What it does:**
```yaml
Job 1: unit-tests
  - Run FastAPI unit tests
  
Job 2: deploy-test (needs: unit-tests)
  - Deploy FastAPI to TEST/DEV environment (Render)
  - Wait for deployment
  
Job 3: integration-tests (needs: deploy-test)
  - Test /health endpoint
  - Test /forecast endpoint with real Databricks
  - Verify end-to-end flow
```

**Key Point:** Integration tests run against **DEV environment**, NOT production!

---

### 3. `deploy.yml` (Production Deployment Workflow)
**Triggers:** On push to main ONLY

**What it does:**
* ✅ Deploy FastAPI to Render PRODUCTION (via deploy hook)
* ✅ Streamlit auto-deploys from GitHub

**Does NOT run tests** - assumes tests passed in test workflows

---

### 4. `deploy-staging.yml` (Staging Deployment Workflow)
**Triggers:** On push to develop/staging/GitConnectionTest

**What it does:**
* ✅ Deploy FastAPI to Render DEV (via deploy hook)
* ✅ Streamlit auto-deploys from GitHub

**Does NOT run tests** - assumes tests passed in test workflows

---

## Why This Is Better

### ❌ OLD WAY (Wrong)
```
deploy.yml:
1. Run unit tests
2. Deploy to production ← DEPLOYS FIRST!
3. Run integration tests ← If this fails, production is already broken!
```

### ✅ NEW WAY (Correct)
```
test-fastapi.yml:
1. Run unit tests
2. Deploy to DEV
3. Run integration tests ← Tests BEFORE production!
4. ✅ Pass = Ready for prod

deploy.yml:
1. Deploy to production ← Only runs if tests passed
```

---

## GitHub Branch Protection (Recommended)

To enforce tests before deployment, set up branch protection:

**GitHub Repo → Settings → Branches → Add rule for `main`:**

* ✅ Require status checks to pass before merging
* ✅ Required checks:
  - `test-streamlit / test`
  - `test-fastapi / unit-tests`
  - `test-fastapi / integration-tests`

This **prevents** `deploy.yml` from running unless all tests pass!

---

## Secret Requirements

### For Testing (test-fastapi.yml)
```
RENDER_DEV_DEPLOY_HOOK = https://api.render.com/deploy/srv-dev-xxx?key=yyy
FASTAPI_DEV_URL = https://your-api-dev.onrender.com
API_KEY_DEV = dev-api-key-here
```

### For Production (deploy.yml)
```
RENDER_PROD_DEPLOY_HOOK = https://api.render.com/deploy/srv-prod-xxx?key=yyy
FASTAPI_PROD_URL = https://your-api.onrender.com  (for manual verification)
API_KEY_PROD = prod-api-key-here  (for manual verification)
```

---

## Execution Flow Example

### Scenario: Push to main

**Step 1:** Push triggers TWO workflows simultaneously:
* `test-streamlit.yml` starts
* `test-fastapi.yml` starts

**Step 2:** test-fastapi.yml does:
1. ✅ Unit tests pass
2. ✅ Deploys to DEV environment
3. ✅ Integration tests pass (tests DEV)

**Step 3:** test-streamlit.yml does:
1. ✅ Unit tests pass

**Step 4:** deploy.yml starts (or waits if branch protection enabled):
1. ✅ Deploys FastAPI to PRODUCTION
2. ✅ Streamlit auto-deploys

**Result:** Production only gets code that passed all tests in DEV!

---

## What Gets Tested Where

| Test Type | Environment | Workflow | When |
|-----------|------------|----------|------|
| Streamlit unit tests | GitHub runner | test-streamlit.yml | Every push/PR |
| FastAPI unit tests | GitHub runner | test-fastapi.yml | Every push/PR |
| Integration tests | DEV (Render) | test-fastapi.yml | After dev deploy |
| Manual verification | PROD (Render) | Manual | After prod deploy |

---

## Benefits

1. **Fail Fast** - Bad code caught in DEV, never reaches prod
2. **Real Environment Testing** - Integration tests run against real Databricks
3. **Separate Concerns** - Testing and deployment are separate workflows
4. **Branch Protection** - Can require tests before allowing deployment
5. **No Prod Testing** - Never test in production; always test in DEV first

---

## Common Questions

**Q: What if I want to deploy without tests?**
A: Use `workflow_dispatch` (manual trigger) on deploy.yml, but NOT RECOMMENDED!

**Q: Do I need separate Render services for dev and prod?**
A: YES! You need two services:
- `retail-forecast-api-dev` (for testing)
- `retail-forecast-api` (for production)

**Q: What about Streamlit testing?**
A: Streamlit is just a frontend - unit tests are sufficient. Integration testing happens at the FastAPI layer.

**Q: Can I skip dev environment?**
A: Not recommended! You'd be testing in production, which is exactly what we're trying to avoid.
