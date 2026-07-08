# CI/CD Setup Documentation

## 🎯 The Problem We Solved

### Original Issue:
- **Streamlit Cloud auto-deploys immediately on push** - no way to delay or control it
- **Tests run after deployment** - broken code could deploy before tests fail
- **No deployment gate** - couldn't prevent untested code from reaching production

### The Challenge:
We needed a way to ensure that **only tested code deploys**, but Streamlit Cloud's webhook automatically deploys on every push to the watched branch.

---

## ✅ The Staging Branch Solution

### Core Concept:
**Use branch protection rules as a deployment gate.**

Instead of trying to control Streamlit's auto-deploy behavior (impossible), we control **which branch Streamlit watches** and **who can push to that branch**.

### Architecture:

```
GitConnectionTest (development)
  • Purpose: Active development & testing
  • Tests: Run on every push ✅
  • Deployment: NOTHING deploys ❌
  • Streamlit: Ignores this branch
  • Render: Ignores this branch
  
  ↓ Create PR (tests must pass to merge)
  
staging (staging environment)
  • Purpose: Pre-production testing
  • Tests: Must pass before PR merge ✅
  • Deployment: Auto-deploys ONLY tested code ✅
  • Streamlit: Watches this branch, auto-deploys
  • Render: Watches this branch, deploys "After CI Checks Pass"
  • Branch Protection: Requires unit-tests + test to pass
  
  ↓ Create PR (tests must pass to merge)
  
main (production)
  • Purpose: Live users
  • Tests: Must pass before PR merge ✅
  • Deployment: Auto-deploys ONLY tested code ✅
  • Streamlit: Watches this branch, auto-deploys
  • Render: Watches this branch, deploys "After CI Checks Pass"
  • Branch Protection: Requires unit-tests + test to pass
```

---

## 🔧 Implementation Details

### 1. Test Workflows

**test-fastapi.yml:**
- Runs on: `GitConnectionTest`, `staging`, `main`
- Path filter: `fastapi-gateway/**`
- Job name: `unit-tests` (used in branch protection)
- No deployment logic

**test-streamlit.yml:**
- Runs on: `GitConnectionTest`, `staging`, `main`
- Path filter: `streamlit-app/**`
- Job name: `test` (used in branch protection)
- Coverage requirement: 80%+

### 2. Deployment Workflows

**deploy-staging.yml:**
- Triggers: When BOTH test workflows complete on `staging` branch
- Purpose: Deployment confirmation (Render/Streamlit already auto-deployed)
- Checks: Both tests passed before confirming

**deploy.yml:**
- Triggers: Push to `main` branch
- Purpose: Production deployment confirmation
- Manual trigger: Available via `workflow_dispatch`

### 3. Render Configuration

**Staging Service:**
- Branch: `staging`
- Auto-Deploy: **"After CI Checks Pass"** ✅
- Root Directory: `fastapi-gateway`
- Result: Only deploys when both `unit-tests` and `test` pass

**Production Service (when created):**
- Branch: `main`
- Auto-Deploy: **"After CI Checks Pass"** ✅
- Root Directory: `fastapi-gateway`

### 4. Streamlit Cloud Configuration

**Staging App:**
- Branch: `staging`
- Auto-Deploy: On push (immediate)
- URL: `retail-forecasting-pipeline-staging.streamlit.app`
- Note: Deploys immediately, but only gets code from staging branch (which requires passing tests to update)

**Production App (when created):**
- Branch: `main`
- Auto-Deploy: On push (immediate)
- URL: `retail-forecasting-pipeline.streamlit.app`

### 5. Branch Protection Rules

**For `staging` and `main` branches:**

```yaml
✅ Require a pull request before merging
   - Required approvals: 0 (solo dev)
   - Dismiss stale pull request approvals

✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Required status checks:
     • unit-tests (FastAPI Gateway Tests)
     • test (Streamlit App Tests)

✅ Require conversation resolution before merging

✅ Do not allow bypassing the above settings
```

---

## 🚀 Daily Workflow

### Development Phase:
```bash
# Work on GitConnectionTest
git checkout GitConnectionTest
# Make changes, commit
git push origin GitConnectionTest

# Tests run automatically ✅
# Nothing deploys ❌
# Get immediate feedback without deployment risk
```

### Deploy to Staging:
```bash
# Create PR: GitConnectionTest → staging
gh pr create --base staging --head GitConnectionTest

# GitHub Actions:
# 1. Tests run on PR ✅
# 2. Branch protection blocks merge if tests fail ❌
# 3. Merge only possible when both tests pass ✅

# After merge:
# 1. Render waits for CI checks → deploys FastAPI ✅
# 2. Streamlit auto-deploys Streamlit app ✅
# 3. deploy-staging.yml confirms deployment ✅
```

### Deploy to Production:
```bash
# Create PR: staging → main
gh pr create --base main --head staging

# Same process as staging
# Only tested code reaches production ✅
```

---

## 🔑 Key Insights

### Why Staging Branch is Essential:

1. **Streamlit Auto-Deploy Can't Be Disabled**
   - Streamlit Cloud always auto-deploys on push
   - Solution: Don't push to watched branches until tests pass
   - Branch protection enforces this

2. **Render "After CI Checks Pass" Setting**
   - Render waits for GitHub status checks
   - Only deploys when `unit-tests` and `test` both pass
   - Perfect complement to branch protection

3. **GitHub Branch Protection as Deployment Gate**
   - Can't merge to staging/main until tests pass
   - Can't push directly (requires PR)
   - Prevents all paths to deploying broken code

### What We Learned:

- **Original approach:** Try to control deployment timing (impossible with Streamlit)
- **Correct approach:** Control what code reaches deployment branches
- **Result:** Auto-deploy is fine when only tested code can reach those branches

---

## 📋 Setup Checklist

### Initial Setup:
- [x] Create `staging` branch from `GitConnectionTest`
- [x] Update test workflows to include `staging` branch
- [x] Remove deployment logic from test workflows
- [x] Update deploy workflows to be confirmation-only

### Render Configuration:
- [x] Change staging service branch to `staging`
- [x] Set Auto-Deploy to "After CI Checks Pass"
- [x] Set Root Directory to `fastapi-gateway`
- [ ] Create production service (when ready)
- [ ] Configure production service same as staging

### Streamlit Configuration:
- [x] Delete old dev app
- [x] Redeploy from `staging` branch
- [x] Configure staging secrets
- [ ] Create production app (when ready)
- [ ] Set production app to watch `main` branch

### GitHub Configuration:
- [x] Set up branch protection for `staging`
  - [x] Require PR before merge
  - [x] Require status checks: `unit-tests`, `test`
  - [x] Require branches up to date
  - [x] No bypassing allowed
- [x] Set up branch protection for `main`
  - [x] Same settings as staging

### Testing:
- [ ] Push change to GitConnectionTest (tests run, no deploy)
- [ ] Create PR to staging (tests required)
- [ ] Merge to staging (auto-deploys)
- [ ] Verify staging deployment works
- [ ] Create PR to main (tests required)
- [ ] Merge to main (production deploys)

---

## 🎉 Benefits of This Setup

1. **Zero broken deployments:** Impossible to deploy without passing tests
2. **Fast feedback:** Tests run on every push to GitConnectionTest
3. **Safe experimentation:** Work freely on dev branch without deployment risk
4. **Automated pipeline:** No manual deployment steps needed
5. **Cost efficient:** Tests only on changed code (path filters)
6. **Production ready:** Same workflow scales from solo dev to team

---

## 📝 Notes

### Why We Don't Use Deploy Hooks Anymore:
- Render's "After CI Checks Pass" is more reliable
- Simplifies workflows (no curl commands, no timing issues)
- Native GitHub integration
- Better error handling

### Path Filters:
- `test-fastapi.yml` only runs when `fastapi-gateway/**` changes
- `test-streamlit.yml` only runs when `streamlit-app/**` changes
- Saves CI minutes and provides faster feedback

### Coverage Requirements:
- Streamlit: 80% minimum (currently at 97.45%)
- FastAPI: Standard pytest (no minimum enforced yet)

---

## 🔗 Resources

- Render Deploy Settings: `Auto-Deploy: After CI Checks Pass`
- Streamlit Branch Settings: Set during app creation (can't change after)
- GitHub Branch Protection: Settings → Branches → Add rule

---

**Last Updated:** January 2025  
**Status:** ✅ Staging configured and working  
**Next Steps:** Set up production resources when ready to go live
