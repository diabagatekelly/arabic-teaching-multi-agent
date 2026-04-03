# Modern Python Tooling Setup

**Philosophy:** Minimal, modern, no redundancy

---

## 📦 Package Management: uv

**Why uv?**
- 10-100x faster than pip
- Automatic virtualenv management
- Replaces pip, pip-tools, virtualenv, poetry
- Created by Astral (same team as ruff)

### Commands

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --dev

# Add a package
uv add langchain

# Add dev dependency
uv add --dev pytest

# Update dependencies
uv sync --upgrade

# Run command in venv
uv run python script.py
uv run pytest
```

**No need to activate venv!** `uv run` handles it automatically.

---

## 🔍 Code Quality: ruff

**Why ruff?**
- Replaces: black, flake8, isort, pylint, pyupgrade
- 10-100x faster than alternatives
- Single tool for linting + formatting

### Commands

```bash
# Lint
ruff check .

# Lint and auto-fix
ruff check --fix .

# Format
ruff format .

# Both (lint + format)
ruff check --fix . && ruff format .
```

### Configuration

See `pyproject.toml`:
- Line length: 100
- Auto-fixes imports, code style
- Ignores line-length warnings (formatter handles it)

---

## 🔒 Type Checking: mypy

**Why mypy?**
- Industry standard for Python type checking
- Catches type errors before runtime
- Enforces strict typing

### Commands

```bash
# Check specific directories
mypy agents/ orchestration/ rag/

# Check everything
mypy .

# Check single file
mypy agents/vocabulary_teacher.py
```

### Configuration

See `pyproject.toml`:
- Strict mode enabled
- Ignores missing imports for 3rd party libs
- Requires type hints on all functions

---

## 🧪 Testing: pytest

**Why pytest?**
- Simple, powerful, extensible
- Industry standard

### Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=agents

# Run only fast tests (skip slow ones)
pytest -m "not slow"
```

---

## 🪝 Pre-commit Hooks

**Automated checks before every commit**

### Setup (one-time)

```bash
pip install pre-commit
pre-commit install
```

### What it does

On every `git commit`:
1. Runs `ruff check --fix` (linting)
2. Runs `ruff format` (formatting)
3. Runs `mypy` (type checking)
4. Blocks commit if checks fail

### Manual run

```bash
# Run on all files
pre-commit run --all-files

# Skip hooks for emergency commit
git commit --no-verify
```

---

## 🚫 What We DON'T Use

### Replaced by uv:
- ❌ pip
- ❌ pip-tools
- ❌ virtualenv
- ❌ poetry
- ❌ pipenv

### Replaced by ruff:
- ❌ black (formatting)
- ❌ flake8 (linting)
- ❌ isort (import sorting)
- ❌ pylint (linting)
- ❌ pyupgrade (syntax upgrades)

### Not needed:
- ❌ autopep8 (ruff does this)
- ❌ yapf (ruff does this)
- ❌ bandit (security - add if needed later)
- ❌ pydocstyle (we enforce minimal docstrings)

---

## 📋 Daily Workflow

### Starting work

```bash
cd ~/Documents/LLMCourse/arabic-teaching-multi-agent

# No need to activate venv! uv handles it
# Just start coding
```

### Before committing

```bash
# Option 1: Let pre-commit handle it
git add .
git commit -m "feat: add feature"
# Pre-commit runs automatically

# Option 2: Run manually first
ruff check --fix . && ruff format .
mypy .
pytest

# Then commit
git add .
git commit -m "feat: add feature"
```

### Adding dependencies

```bash
# Add runtime dependency
uv add chromadb

# Add dev dependency
uv add --dev pytest-cov

# Dependencies are automatically written to pyproject.toml
# And synced to .venv/
```

---

## 🔧 IDE Integration

### VS Code

Install extensions:
- **Ruff** (`charliermarsh.ruff`)
- **Mypy Type Checker** (`ms-python.mypy-type-checker`)
- **Python** (`ms-python.python`)

Settings (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  },
  "ruff.lint.args": ["--config=pyproject.toml"],
  "mypy-type-checker.args": ["--config-file=pyproject.toml"]
}
```

### Cursor (same as VS Code)

### PyCharm

- Ruff plugin available
- Built-in mypy integration
- Set project interpreter to `.venv/bin/python`

---

## 📊 Comparison

| Task | Old Way | Modern Way (uv + ruff) |
|------|---------|----------------------|
| **Create venv** | `python -m venv venv && source venv/bin/activate` | `uv sync` |
| **Install deps** | `pip install -r requirements.txt` | `uv sync` |
| **Add package** | `pip install X && pip freeze > requirements.txt` | `uv add X` |
| **Format code** | `black . && isort .` | `ruff format .` |
| **Lint code** | `flake8 . && pylint .` | `ruff check .` |
| **Type check** | `mypy .` | `mypy .` (same) |
| **Run tests** | `source venv/bin/activate && pytest` | `uv run pytest` |

---

## 🎯 Our Minimal Stack

**Total tools: 4**
1. **uv** - Package management
2. **ruff** - Linting + formatting
3. **mypy** - Type checking
4. **pytest** - Testing

**Optional:**
5. **pre-commit** - Automate the above

That's it! No bloat, all modern, all fast.

---

## 📚 References

- [uv docs](https://docs.astral.sh/uv/)
- [ruff docs](https://docs.astral.sh/ruff/)
- [mypy docs](https://mypy.readthedocs.io/)
- [pytest docs](https://docs.pytest.org/)
- [pre-commit docs](https://pre-commit.com/)

---

*Last updated: April 3, 2026*
