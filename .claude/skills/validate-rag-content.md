---
name: validate-rag-content
description: Validate lesson/exercise markdown files for RAG parser compatibility
args:
  - name: file_path
    description: Path to lesson or exercise .md file to validate
    required: false
---

# RAG Content Validation Skill

**Purpose:** Ensure new/updated lesson and exercise markdown files are compatible with the `MarkdownParser` and will create optimal chunks for RAG retrieval.

## What This Validates

1. **Frontmatter Format**
   - Valid YAML between `---` delimiters
   - Required fields present (lesson_number, lesson_name OR exercise_type)
   - No syntax errors

2. **Section Structure**
   - Uses `##` (level 2) headers for main sections
   - Headers are properly formatted
   - Sections are reasonably sized (<3000 chars)

3. **Chunk Size Analysis**
   - Preview how the parser will chunk the file
   - Report chunk sizes (chars and estimated tokens)
   - Flag chunks that are too large (>3000 chars / >750 tokens)
   - Flag chunks that are too small (<200 chars / <50 tokens)

4. **Content Quality**
   - UTF-8 encoding (supports Arabic text)
   - No problematic characters that break parsing
   - Proper markdown formatting

## Usage

### Validate a single file:
```
/validate-rag-content data/rag_database/lessons/lesson_02_pronouns.md
```

Or directly:
```bash
python scripts/validate_rag_content.py data/rag_database/lessons/lesson_02_pronouns.md
```

### Validate all files in a directory:
```
/validate-rag-content data/rag_database/lessons
```

### Validate with no args (validates all RAG content):
```
/validate-rag-content
```

## Validation Process

1. **Read the file(s)** to validate
2. **Parse with MarkdownParser** to generate chunks
3. **Analyze each chunk:**
   - Character count
   - Estimated token count (chars ÷ 4)
   - Section title
4. **Report findings:**
   - ✅ PASS: All chunks within acceptable range (200-3000 chars, optimal 400-2000)
   - ⚠️ WARNING: Some chunks outside optimal range (<200 or >2000 chars)
   - ❌ FAIL: Chunks too large (>3000 chars) or invalid structure

## Output Format

```
📋 Validating: data/rag_database/lessons/lesson_02_pronouns.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Frontmatter: Valid YAML
   • lesson_number: 2
   • lesson_name: Subject Pronouns
   • doc_type: lesson

✅ Section Structure: 6 sections found
   • Overview (450 chars / ~112 tokens)
   • Pronouns Table (820 chars / ~205 tokens)
   • Usage Rules (1,240 chars / ~310 tokens)
   • Common Mistakes (680 chars / ~170 tokens)
   • Practice Examples (1,100 chars / ~275 tokens)
   • Summary (390 chars / ~97 tokens)

📊 Chunk Analysis:
   Total chunks: 6
   Size range: 390 - 1,240 chars (97 - 310 tokens)
   ✅ All chunks in optimal range (400-3000 chars)

✅ PASS: File is RAG-ready!
```

### If there are issues:

```
⚠️ WARNING: Large section detected

Section: "Detailed Examples"
Size: 3,420 chars (~855 tokens)
Recommendation: Split into smaller subsections using ##

Suggested fix:
  ## Detailed Examples - Part 1
  [first half of content]
  
  ## Detailed Examples - Part 2
  [second half of content]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Guidelines for Fixing Issues

### Problem: Section too large (>3000 chars)

**Solution:** Split into multiple `##` sections
```markdown
Before:
## Long Section
[3500 characters of content...]

After:
## Long Section - Part 1
[1800 characters...]

## Long Section - Part 2
[1700 characters...]
```

### Problem: Section too small (<200 chars)

**Solution:** Merge with related section or expand content
```markdown
Before:
## Tiny Section
Just one sentence.

## Another Tiny Section
Another sentence.

After:
## Combined Section
Just one sentence. Another sentence. [expanded content...]
```

### Problem: Invalid frontmatter

**Solution:** Fix YAML syntax
```markdown
Before:
---
lesson_number 2
lesson_name: Pronouns
---

After:
---
lesson_number: 2
lesson_name: Pronouns
---
```

### Problem: Using wrong header level

**Solution:** Use `##` for main sections
```markdown
Before:
### Grammar Rule
Content...

After:
## Grammar Rule
Content...
```

## Optimal Chunk Size Guidelines

**Target Range:** 400-2000 characters (100-500 tokens)

| Size Category | Chars | Tokens | Status | Action |
|---------------|-------|--------|--------|--------|
| Too Small | <200 | <50 | ⚠️ WARNING | Merge or expand |
| Acceptable Small | 200-400 | 50-100 | ✅ PASS | OK, but prefer larger |
| **Optimal** | **400-2000** | **100-500** | **✅ PASS** | **Perfect!** |
| Acceptable Large | 2000-3000 | 500-750 | ⚠️ WARNING | OK, but consider splitting |
| Too Large | >3000 | >750 | ❌ FAIL | Split required |

## Integration with Content Creation

**When creating new lessons:**
1. Write the lesson content
2. Run `/validate-rag-content <your-file.md>`
3. Fix any issues reported
4. Re-validate until all checks pass
5. Commit the file

**Before committing changes:**
```bash
# Validate all RAG content
/validate-rag-content

# If all pass, commit
git add data/rag_database/
git commit -m "Add lesson 2 content (validated for RAG)"
```

## Implementation Notes

This skill should:
1. Use the validation script at `scripts/validate_rag_content.py`
2. The script uses `MarkdownParser` from `src/rag/markdown_parser.py`
3. Parse the file(s) to generate chunks
4. Analyze chunk sizes and structure
5. Report in a clear, actionable format
6. Suggest specific fixes for any issues found

**Code location:** `scripts/validate_rag_content.py` (developer tool, excluded from test coverage)

---

**Remember:** The parser splits by `##` headers. Each section becomes one chunk. Keep sections between 400-2000 chars for optimal RAG retrieval quality!
