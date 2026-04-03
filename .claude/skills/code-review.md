# Code Review Skill

Perform comprehensive code quality review with strict standards enforcement.

## Usage

```
/review <file_path>
```

Or review all changed files:
```
/review
```

## Review Standards

### 1. Comment Standards
- **NO unnecessary comments**
- Comments only for:
  - Complex algorithms requiring explanation
  - Non-obvious business logic
  - Public API documentation (docstrings)
- ❌ **Never comment:**
  - Obvious code (`# increment counter` for `count += 1`)
  - What the code does (code should be self-explanatory)
  - Redundant type information already in type hints

### 2. Function Standards
- **Maximum 20 lines preferred**
- Single responsibility principle
- Clear, descriptive names (no comments needed)
- Extract complex logic into well-named helper functions
- Early returns over deep nesting

### 3. Architecture Standards
- Clean separation of concerns
- No circular dependencies
- Interface-based design for agents
- Dependency injection over global state
- Single source of truth for configuration

### 4. Type Hints
- **Required** for all function signatures
- **Required** for class attributes
- Use `from __future__ import annotations` for forward references
- Prefer `list[str]` over `List[str]` (Python 3.10+)
- Use Pydantic models for complex data structures

### 5. Docstrings
- **Required** for public functions/classes only
- **NOT required** for private functions (self-explanatory code)
- Format: Google-style docstrings
- Include: brief description, Args, Returns
- ❌ **Never** repeat type information already in type hints

## Instructions

When reviewing code:

1. **Scan for over-commenting**
   - Flag any comment that explains what code does (not why)
   - Flag comments that duplicate type hints
   - Flag obvious comments

2. **Check function length**
   - If >20 lines, suggest refactoring
   - Identify extractable logic
   - Propose well-named helper functions

3. **Analyze architecture**
   - Check for tight coupling
   - Verify interface usage
   - Check dependency direction
   - Flag god objects/classes

4. **Validate type hints**
   - All public functions must have hints
   - Check for `Any` usage (should be specific)
   - Verify Pydantic usage for complex data

5. **Assess succinctness**
   - Identify verbose implementations
   - Suggest more Pythonic alternatives
   - Flag repeated code (DRY violations)
   - Check for unnecessary intermediate variables

## Output Format

Provide feedback in this structure:

```markdown
## Code Review: <file_name>

### ✅ Strengths
- [What's good]

### ❌ Issues Found

#### 1. Over-commenting
**Line X:** Comment is unnecessary
```python
# Bad
count += 1  # increment counter

# Good  
count += 1
```

#### 2. Function Too Long
**Function `process_data` (45 lines):** Exceeds 20-line guideline
**Suggestion:** Extract validation logic into `_validate_input()`

#### 3. Missing Type Hints
**Line Y:** Function signature lacks type hints
```python
# Bad
def calculate(x, y):
    return x + y

# Good
def calculate(x: float, y: float) -> float:
    return x + y
```

#### 4. Verbose Implementation
**Lines Z-Z+5:** Can be simplified
```python
# Verbose
result = []
for item in items:
    if item.is_valid:
        result.append(item.value)
return result

# Succinct
return [item.value for item in items if item.is_valid]
```

### 🔧 Refactoring Suggestions
1. [Specific suggestion with code example]
2. [Specific suggestion with code example]

### 📊 Summary
- Comments: X unnecessary
- Functions >20 lines: Y
- Missing type hints: Z
- Architecture issues: W
```

## Example

### Input
```python
# agents/vocabulary_teacher.py
class VocabularyTeacher:
    # This function teaches vocabulary to the student
    def teach_vocabulary(self, lesson_number, vocabulary_list):
        # Loop through all the vocabulary words
        for word in vocabulary_list:
            # Create a new word object
            word_obj = Word(word)
            # Add the word to the lesson
            self.lesson.add_word(word_obj)
            # Log that we added the word
            logger.info(f"Added word: {word}")
        # Return success
        return True
```

### Output
```markdown
## Code Review: agents/vocabulary_teacher.py

### ❌ Issues Found

#### 1. Excessive Comments (7 unnecessary)
Every single line has an obvious comment. Code should be self-explanatory.

**Lines 2-12:** Remove all comments

#### 2. Missing Type Hints
**Line 3:** No type hints on function signature

#### 3. Verbose Implementation
**Lines 5-8:** Unnecessary intermediate variable and loop

### 🔧 Refactored Version
```python
from __future__ import annotations
from pydantic import BaseModel

class VocabularyTeacher:
    def teach_vocabulary(
        self, 
        lesson_number: int, 
        vocabulary_list: list[str]
    ) -> bool:
        for word in vocabulary_list:
            self.lesson.add_word(Word(word))
            logger.info(f"Added word: {word}")
        return True
```

**Changes:**
- Removed 7 unnecessary comments
- Added type hints
- Removed intermediate `word_obj` variable
- Code is now self-explanatory

### 📊 Summary
- Comments removed: 7
- Type hints added: 3
- Lines reduced: 12 → 6
```

## Integration with Automated Tools

This skill complements automated tooling:

**Ruff** (linting + formatting):
```bash
ruff check .          # Lint
ruff format .         # Format
ruff check --fix .    # Auto-fix
```

**Mypy** (type checking):
```bash
mypy agents/ orchestration/ rag/
```

**Pre-commit** (runs both automatically):
```bash
pre-commit run --all-files
```

**This skill focuses on:**
- Comment quality (tools don't check this)
- Function length (architectural concern)
- Architecture patterns (higher-level than tools)
- Code readability (tools can't judge this)

**Workflow:**
1. Run `/review` for architecture & comment checks
2. Run `ruff check --fix .` for linting
3. Run `mypy .` for type checking
4. Sourcery for advanced refactoring (optional)

## Notes

- This skill enforces **strict** standards
- Prioritize readability over cleverness
- Prefer explicit over implicit (except for obvious cases)
- "Code should read like well-written prose" - Martin Fowler
