"""Tests for Arabic text matching utilities."""

import pytest

from src.evaluation.utils.arabic_text_matching import (
    check_learned_items_usage,
    extract_arabic_words,
    extract_vocab_from_item,
    format_usage_result,
    remove_harakaat,
    vocab_appears_in_text,
)


class TestRemoveHarakaat:
    """Test harakaat removal."""

    @pytest.mark.parametrize(
        "input_text,expected,diacritic_type",
        [
            ("كَتَبَ", "كتب", "fatha"),
            ("كُتُبٌ", "كتب", "damma"),
            ("الكِتَاب", "الكتاب", "kasra"),
            ("مَدْرَسَة", "مدرسة", "sukun"),
            ("مُدَرِّس", "مدرس", "shadda"),
            ("كِتَابٌ", "كتاب", "tanween_damma"),
            ("كِتَابًا", "كتابا", "tanween_fatha"),
            ("كِتَابٍ", "كتاب", "tanween_kasra"),
        ],
    )
    def test_remove_various_harakaat(self, input_text, expected, diacritic_type):
        """Remove all types of diacritics."""
        assert remove_harakaat(input_text) == expected

    def test_mixed_text_with_harakaat(self):
        """Remove harakaat from realistic text."""
        assert remove_harakaat("القَلَمُ في الحَقِيبَةِ") == "القلم في الحقيبة"

    def test_text_without_harakaat(self):
        """Text without harakaat remains unchanged."""
        assert remove_harakaat("الكتاب") == "الكتاب"

    def test_empty_string(self):
        """Empty string handled correctly."""
        assert remove_harakaat("") == ""


class TestExtractArabicWords:
    """Test Arabic word extraction."""

    def test_extract_from_mixed_text(self):
        """Extract Arabic from English/Arabic mix."""
        words = extract_arabic_words("Translate: القَلَم")
        assert words == ["القلم"]

    def test_extract_from_transliteration(self):
        """Extract Arabic from transliteration format."""
        words = extract_arabic_words("كِتَاب (kitaab) - book")
        assert words == ["كتاب"]

    def test_extract_multiple_words(self):
        """Extract multiple Arabic words."""
        words = extract_arabic_words("القَلَم في الحَقِيبَة")
        assert words == ["القلم", "في", "الحقيبة"]

    def test_no_arabic_text(self):
        """No Arabic in text returns empty list."""
        words = extract_arabic_words("Gender agreement rule")
        assert words == []

    def test_pure_arabic_text(self):
        """Pure Arabic text."""
        words = extract_arabic_words("أنا أكتب في المدرسة")
        assert len(words) == 4


class TestExtractVocabFromItem:
    """Test vocabulary extraction from learned items."""

    def test_extract_with_transliteration(self):
        """Extract vocab with transliteration."""
        assert extract_vocab_from_item("كِتَاب (kitaab) - book") == "كتاب"

    def test_extract_with_definite_article(self):
        """Extract vocab with definite article."""
        assert extract_vocab_from_item("القَلَم (al-qalam) - the pen") == "القلم"

    def test_extract_pure_arabic(self):
        """Extract from pure Arabic."""
        assert extract_vocab_from_item("المَدْرَسَة") == "المدرسة"

    def test_extract_sentence(self):
        """Extract first word from sentence."""
        result = extract_vocab_from_item("الكِتَاب على الطَاوِلَة (the book is on the table)")
        assert result == "الكتاب"

    def test_non_arabic_item(self):
        """Non-Arabic item returns empty string."""
        assert extract_vocab_from_item("Gender agreement rule") == ""

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert extract_vocab_from_item("") == ""


class TestVocabAppearsInText:
    """Test vocabulary matching in text."""

    def test_exact_match_with_harakaat(self):
        """Match vocab despite harakaat differences."""
        assert vocab_appears_in_text("قلم", "القَلَم") is True

    def test_match_with_definite_article(self):
        """Match vocab within definite form."""
        assert vocab_appears_in_text("كتاب", "الكِتَاب") is True

    def test_match_in_sentence(self):
        """Match vocab in context."""
        assert vocab_appears_in_text("مدرسة", "في المدرسة") is True

    def test_match_with_preposition(self):
        """Match vocab with attached preposition."""
        assert vocab_appears_in_text("طاولة", "على الطَّاوِلَة") is True

    def test_no_match(self):
        """Vocab not in text."""
        assert vocab_appears_in_text("قطة", "الكلب") is False

    def test_partial_match(self):
        """Substring matching works."""
        assert vocab_appears_in_text("درس", "المَدْرَسَة") is True

    def test_case_with_both_harakaat(self):
        """Both vocab and text have harakaat."""
        assert vocab_appears_in_text("الكِتَاب", "الكِتَابُ على الطَّاوِلَةِ") is True

    def test_empty_vocab(self):
        """Empty vocab returns False."""
        assert vocab_appears_in_text("", "النص") is False

    def test_empty_text(self):
        """Empty text returns False."""
        assert vocab_appears_in_text("كتاب", "") is False


class TestCheckLearnedItemsUsage:
    """Test learned items usage checking (main function)."""

    def test_single_item_used(self):
        """Single learned item is used."""
        text = "الكِتَاب"
        items = ["كِتَاب (kitaab) - book"]

        passed, used, unused = check_learned_items_usage(text, items)

        assert passed is True
        assert len(used) == 1
        assert len(unused) == 0

    def test_single_item_not_used(self):
        """Single learned item not used."""
        text = "القَلَم"
        items = ["كِتَاب (kitaab) - book"]

        passed, used, unused = check_learned_items_usage(text, items)

        assert passed is False
        assert len(used) == 0
        assert len(unused) == 1

    def test_multiple_items_all_used(self):
        """All learned items used."""
        text = "الكِتَاب على الطَّاوِلَة"
        items = ["كِتَاب (kitaab) - book", "طَاوِلَة (taawila) - table"]

        passed, used, unused = check_learned_items_usage(text, items)

        assert passed is True
        assert len(used) == 2
        assert len(unused) == 0

    def test_multiple_items_partial_used(self):
        """Some learned items used."""
        text = "القَلَم في الحَقِيبَة"
        items = ["كِتَاب (kitaab) - book", "قَلَم (qalam) - pen", "مَدْرَسَة (madrasa) - school"]

        passed, used, unused = check_learned_items_usage(text, items)

        assert passed is True  # At least one used
        assert len(used) == 1
        assert "قَلَم (qalam) - pen" in used

    def test_real_world_example_from_eval(self):
        """Real example from evaluation that was failing."""
        # This was marked as "none used" but should pass!
        text = "أنا أكتب في المدرسة"
        items = ["كِتَاب (kitaab) - book", "قَلَم (qalam) - pen", "مَدْرَسَة (madrasa) - school"]

        passed, used, unused = check_learned_items_usage(text, items)

        assert passed is True
        assert len(used) == 1
        assert "مَدْرَسَة (madrasa) - school" in used

    def test_real_world_example_2(self):
        """Another real example: direct vocab match."""
        text = "القَلَم"
        items = ["كِتَاب (kitaab) - book", "قَلَم (qalam) - pen", "مَدْرَسَة (madrasa) - school"]

        passed, used, unused = check_learned_items_usage(text, items)

        assert passed is True
        assert len(used) == 1
        assert "قَلَم (qalam) - pen" in used

    def test_require_all_items(self):
        """Test require_all flag."""
        text = "الكِتَاب"
        items = ["كِتَاب (kitaab) - book", "قَلَم (qalam) - pen"]

        passed, used, unused = check_learned_items_usage(text, items, require_all=True)

        assert passed is False  # Only 1/2 used
        assert len(used) == 1
        assert len(unused) == 1

    def test_min_usage_count(self):
        """Test minimum usage count."""
        text = "الكِتَاب"
        items = ["كِتَاب (kitaab) - book", "قَلَم (qalam) - pen", "مَدْرَسَة (madrasa) - school"]

        # Require at least 2 items
        passed, used, unused = check_learned_items_usage(text, items, min_usage_count=2)

        assert passed is False  # Only 1 used, need 2
        assert len(used) == 1

    def test_non_arabic_items_ignored(self):
        """Non-Arabic learned items (grammar rules) are ignored."""
        text = "الكِتَابُ كَبِيرٌ"
        items = ["كِتَاب (kitaab) - book", "Gender agreement rule"]

        passed, used, unused = check_learned_items_usage(text, items)

        assert passed is True
        assert len(used) == 1
        # Grammar rule should not be in unused (it's skipped)
        assert "Gender agreement rule" not in unused


class TestFormatUsageResult:
    """Test result formatting."""

    def test_format_all_used(self):
        """Format when all items used."""
        used = ["كتاب (book)", "قلم (pen)"]
        unused = []

        result = format_usage_result(True, used, unused)

        assert "✓" in result
        assert "all 2 used" in result

    def test_format_none_used(self):
        """Format when none used."""
        used = []
        unused = ["كتاب (book)", "قلم (pen)"]

        result = format_usage_result(False, used, unused)

        assert "✗" in result
        assert "none used" in result
        assert "expected 2" in result

    def test_format_partial_used(self):
        """Format when some used."""
        used = ["كتاب (book)"]
        unused = ["قلم (pen)", "مدرسة (school)"]

        result = format_usage_result(True, used, unused)

        assert "✓" in result
        assert "1/3 used" in result

    def test_format_shows_vocab(self):
        """Format shows summary when all items used."""
        used = ["كتاب (book)"]
        unused = []

        result = format_usage_result(True, used, unused)

        assert "✓" in result
        assert "all 1 used" in result
