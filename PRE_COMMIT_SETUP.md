# Pre-Commit Hooks Setup Guide

## Problem Solved
**Before:** GitHub Actions auto-formatted code and created extra commits, causing push conflicts  
**After:** Code is formatted locally before commit, no extra GitHub commits!

---

## One-Time Setup (Run Locally)

```bash
# 1. Install pre-commit tool
pip install pre-commit

# 2. Navigate to your project directory
cd /path/to/retail-forecasting-pipeline

# 3. Install the git hooks
pre-commit install

# Done! ✅
```

---

## How It Works

### Every Time You Commit:
```bash
git add .
git commit -m "your message"

# Pre-commit automatically:
# 1. Runs Black formatter
# 2. Runs isort (import sorter)
# 3. If changes made → commit is paused, files are formatted
# 4. You review the changes, then commit again
```

### Example Output:
```
$ git commit -m "add new feature"
black....................................................................Passed
isort....................................................................Passed
[GitConnectionTest abc123] add new feature
 2 files changed, 10 insertions(+)
```

---

## What Changed

### ✅ Added:
* `.pre-commit-config.yaml` - Defines formatting rules
* Local pre-commit hooks (after running `pre-commit install`)

### ❌ Disabled:
* `.github/workflows/auto-format.yml` - No longer creates auto-format commits

### ✅ Still Active:
* `.github/workflows/lint.yml` - Still checks formatting in CI (won't create commits)
* All test workflows
* All deployment workflows

---

## Benefits

1. **No More Conflicts** - Local and remote stay in sync
2. **Faster Feedback** - See formatting issues before pushing
3. **Cleaner History** - No "auto-format" commits
4. **Consistent Style** - Same rules locally and in CI

---

## Troubleshooting

### "pre-commit command not found"
```bash
pip install pre-commit
```

### Skip hooks temporarily (not recommended)
```bash
git commit -m "message" --no-verify
```

### Manually run hooks on all files
```bash
pre-commit run --all-files
```

### Update hook versions
```bash
pre-commit autoupdate
```

---

## FAQ

**Q: Do I need to commit .pre-commit-config.yaml?**  
A: YES! This file should be in the repo so everyone uses the same formatting.

**Q: What if my teammate doesn't install pre-commit?**  
A: lint.yml will catch it in CI (but won't auto-fix)

**Q: Can I use this with other projects?**  
A: Absolutely! Pre-commit works with any git repo.

---

## Next Steps

1. Run `pip install pre-commit && pre-commit install` locally
2. Commit the new files (.pre-commit-config.yaml, PRE_COMMIT_SETUP.md)
3. Push - no more auto-format commits! ✅
