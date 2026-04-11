# Development Workflow

## Branch Strategy

```
main (stable)
 └── dev (integration)
      └── phase-N/feature-name (feature branches)
```

## Creating a PR

1. **Create feature branch from dev:**
   ```bash
   git checkout dev
   git pull
   git checkout -b phase-1/feature-name
   ```

2. **Make changes and commit:**
   ```bash
   git add -A
   git commit -m "Description"
   ```

3. **Run review skill locally (in Claude Code):**
   ```
   /review
   ```
   This runs the code review skill on your changes before creating the PR.

4. **Push and create PR:**
   ```bash
   git push -u origin phase-1/feature-name
   gh pr create --base dev --title "Title" --body "Description"
   ```

5. **Merge when approved:**
   ```bash
   gh pr merge <pr-number> --merge --delete-branch
   ```

## Pre-commit Hooks

Already configured in `.pre-commit-config.yaml`:
- ✅ ruff (linting)
- ✅ ruff-format (formatting)
- ✅ mypy (type checking)
- ✅ pytest with 95% coverage (when src/ modules exist)

These run automatically on `git commit`.

## Running /review Skill

**Before creating PR:**
```bash
# In Claude Code terminal or chat:
/review
```

This will analyze your changes and provide feedback before you push.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_evaluation.py
```

## Evaluation Pipeline

```bash
# Run baseline evaluation (Phase 1)
python -m src.evaluation.baseline

# After fine-tuning (Phase 2), evaluate fine-tuned model
python -m src.evaluation.deepeval_pipeline
```

---

**Key Point:** Run `/review` locally before creating PRs. No GitHub Actions needed.
