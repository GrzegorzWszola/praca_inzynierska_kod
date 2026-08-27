import unittest
from unittest.mock import MagicMock
import ebooklib
from book_parser.core import ProcessingCore, StandardProcessor, BestEffortProcessor, MATTER_TO_SKIP


class DummyItem:
    """Mock item representing an epub spine item."""
    def __init__(self, name: str, html_content: str, item_type: int = ebooklib.ITEM_DOCUMENT):
        self._name = name
        self._content = html_content.encode("utf-8")
        self._type = item_type

    def get_name(self) -> str:
        return self._name

    def get_content(self) -> bytes:
        return self._content

    def get_type(self) -> int:
        return self._type


class TestProcessingCoreNormalize(unittest.TestCase):
    """Unit tests for ProcessingCore.normalize method."""

    def setUp(self):
        self.processor = StandardProcessor()

    def test_curly_double_quotes_converted_to_straight_quotes(self):
        raw = "\u201cHello World\u201d"
        expected = '"Hello World"'
        self.assertEqual(self.processor.normalize(raw), expected)

    def test_curly_single_quotes_converted_to_apostrophe(self):
        raw = "\u2018It\u2019s working\u2019"
        expected = "'It's working'"
        self.assertEqual(self.processor.normalize(raw), expected)

    def test_dashes_converted_to_space_hyphen_space(self):
        raw_em = "word\u2014another"
        raw_en = "word\u2013another"
        expected = "word - another"
        self.assertEqual(self.processor.normalize(raw_em), expected)
        self.assertEqual(self.processor.normalize(raw_en), expected)

    def test_zero_width_and_invisible_characters_removed(self):
        raw = "word\ufeffwith\u200bhidden\u00adchars"
        expected = "wordwithhiddenchars"
        self.assertEqual(self.processor.normalize(raw), expected)

    def test_multiple_spaces_collapsed(self):
        raw = "Multiple    spaces    between    words"
        expected = "Multiple spaces between words"
        self.assertEqual(self.processor.normalize(raw), expected)

    def test_strip_leading_and_trailing_whitespace(self):
        raw = "   text with outer spaces   "
        expected = "text with outer spaces"
        self.assertEqual(self.processor.normalize(raw), expected)

    def test_unicode_nfc_normalization(self):
        decomposed = "cafe\u0301"
        composed = "café"
        self.assertEqual(self.processor.normalize(decomposed), composed)


class TestStandardProcessorExtract(unittest.TestCase):
    """Unit tests for StandardProcessor.extract method."""

    def setUp(self):
        self.processor = StandardProcessor()

    def test_extract_p_tags(self):
        html = """
        <html>
            <body>
                <p>First paragraph.</p>
                <p>Second paragraph with \u201cquotes\u201d.</p>
            </body>
        </html>
        """
        item = DummyItem("chapter1.xhtml", html)
        result = self.processor.extract(item)
        expected = [
            "First paragraph.",
            'Second paragraph with "quotes".'
        ]
        self.assertEqual(result, expected)

    def test_extract_leaf_div_tags(self):
        html = """
        <html>
            <body>
                <div>Direct text in div.</div>
            </body>
        </html>
        """
        item = DummyItem("chapter1.xhtml", html)
        result = self.processor.extract(item)
        self.assertEqual(result, ["Direct text in div."])

    def test_skip_container_divs(self):
        html = """
        <html>
            <body>
                <div class="container">
                    <p>Paragraph inside div.</p>
                </div>
            </body>
        </html>
        """
        item = DummyItem("chapter1.xhtml", html)
        result = self.processor.extract(item)
        self.assertEqual(result, ["Paragraph inside div."])

    def test_skip_empty_tags(self):
        html = """
        <html>
            <body>
                <p></p>
                <p>   </p>
                <p>Valid content</p>
                <div></div>
            </body>
        </html>
        """
        item = DummyItem("chapter1.xhtml", html)
        result = self.processor.extract(item)
        self.assertEqual(result, ["Valid content"])


class TestStandardProcessorProcess(unittest.TestCase):
    """Unit tests for StandardProcessor.process method with mock EpubBook."""

    def setUp(self):
        self.processor = StandardProcessor()

    def test_skips_matter_to_skip(self):
        title_item = DummyItem("titlepage.xhtml", "<p>Book Title</p>")
        toc_item = DummyItem("toc.xhtml", "<p>Table of Contents</p>")
        ch1_item = DummyItem("chapter-1.xhtml", "<p>Chapter 1 text.</p>")
        ch2_item = DummyItem("chapter-2.xhtml", "<p>Chapter 2 text.</p>")
        colophon_item = DummyItem("colophon.xhtml", "<p>Colophon notes</p>")

        book_mock = MagicMock()
        book_mock.spine = [
            ("id_title", "yes"),
            ("id_toc", "yes"),
            ("id_ch1", "yes"),
            ("id_ch2", "yes"),
            ("id_colophon", "yes")
        ]

        item_map = {
            "id_title": title_item,
            "id_toc": toc_item,
            "id_ch1": ch1_item,
            "id_ch2": ch2_item,
            "id_colophon": colophon_item
        }
        book_mock.get_item_with_id.side_effect = lambda idref: item_map[idref]

        chapters = self.processor.process(book_mock)

        self.assertEqual(len(chapters), 2)
        self.assertIn(1, chapters)
        self.assertIn(2, chapters)
        self.assertEqual(chapters[1], ["Chapter 1 text."])
        self.assertEqual(chapters[2], ["Chapter 2 text."])

    def test_matter_to_skip_contains_expected_keywords(self):
        expected_keys = {"titlepage", "imprint", "colophon", "uncopyright", "halftitlepage",
                         "copyright", "dedication", "epigraph", "toc", "nav", "cover",
                         "acknowledgments", "endnotes", "loi"}
        self.assertTrue(expected_keys.issubset(MATTER_TO_SKIP))


class TestBestEffortProcessorRomanToInt(unittest.TestCase):
    """Unit tests for BestEffortProcessor.roman_to_int method."""

    def setUp(self):
        self.processor = BestEffortProcessor()

    def test_single_numerals(self):
        self.assertEqual(self.processor.roman_to_int("I"), 1)
        self.assertEqual(self.processor.roman_to_int("V"), 5)
        self.assertEqual(self.processor.roman_to_int("X"), 10)
        self.assertEqual(self.processor.roman_to_int("L"), 50)
        self.assertEqual(self.processor.roman_to_int("C"), 100)
        self.assertEqual(self.processor.roman_to_int("D"), 500)
        self.assertEqual(self.processor.roman_to_int("M"), 1000)

    def test_additive_combinations(self):
        self.assertEqual(self.processor.roman_to_int("II"), 2)
        self.assertEqual(self.processor.roman_to_int("III"), 3)
        self.assertEqual(self.processor.roman_to_int("VI"), 6)
        self.assertEqual(self.processor.roman_to_int("VII"), 7)
        self.assertEqual(self.processor.roman_to_int("VIII"), 8)
        self.assertEqual(self.processor.roman_to_int("XV"), 15)
        self.assertEqual(self.processor.roman_to_int("XX"), 20)
        self.assertEqual(self.processor.roman_to_int("LX"), 60)
        self.assertEqual(self.processor.roman_to_int("CL"), 150)
        self.assertEqual(self.processor.roman_to_int("MCC"), 1200)

    def test_subtractive_combinations(self):
        self.assertEqual(self.processor.roman_to_int("IV"), 4)
        self.assertEqual(self.processor.roman_to_int("IX"), 9)
        self.assertEqual(self.processor.roman_to_int("XL"), 40)
        self.assertEqual(self.processor.roman_to_int("XC"), 90)
        self.assertEqual(self.processor.roman_to_int("CD"), 400)
        self.assertEqual(self.processor.roman_to_int("CM"), 900)

    def test_complex_combinations(self):
        self.assertEqual(self.processor.roman_to_int("XIV"), 14)
        self.assertEqual(self.processor.roman_to_int("XLII"), 42)
        self.assertEqual(self.processor.roman_to_int("XCIX"), 99)
        self.assertEqual(self.processor.roman_to_int("CDXLIV"), 444)
        self.assertEqual(self.processor.roman_to_int("MCMLXXXIV"), 1984)
        self.assertEqual(self.processor.roman_to_int("MCMXCIV"), 1994)
        self.assertEqual(self.processor.roman_to_int("MMXXVI"), 2026)

    def test_case_insensitivity(self):
        self.assertEqual(self.processor.roman_to_int("iv"), 4)
        self.assertEqual(self.processor.roman_to_int("xiv"), 14)
        self.assertEqual(self.processor.roman_to_int("mcmxciv"), 1994)
        self.assertEqual(self.processor.roman_to_int("Xv"), 15)

    def test_empty_string_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.processor.roman_to_int("")
        self.assertIn("Cannot convert empty string", str(ctx.exception))

    def test_invalid_characters_raise_value_error(self):
        for invalid in ["A", "123", "IXZ", "IV B"]:
            with self.assertRaises(ValueError) as ctx:
                self.processor.roman_to_int(invalid)
            self.assertIn("Invalid Roman numeral character", str(ctx.exception))


class TestBestEffortProcessorExtract(unittest.TestCase):
    """Unit tests for BestEffortProcessor.extract method."""

    def setUp(self):
        self.processor = BestEffortProcessor()

    def test_extract_chapter_with_roman_numerals(self):
        html = """
        <html>
            <body>
                <h1>CHAPTER I</h1>
                <p>First paragraph of chapter one.</p>
                <p>Second paragraph of chapter one.</p>
            </body>
        </html>
        """
        item = DummyItem("chapter1.xhtml", html)
        self.processor.extract(item)

        self.assertIn(1, self.processor.chapters)
        self.assertEqual(
            self.processor.chapters[1],
            ["First paragraph of chapter one.", "Second paragraph of chapter one."]
        )

    def test_extract_chapter_with_arabic_digits(self):
        html = """
        <html>
            <body>
                <h2>Chapter 12</h2>
                <p>First paragraph of chapter 12.</p>
            </body>
        </html>
        """
        item = DummyItem("chapter12.xhtml", html)
        self.processor.extract(item)

        self.assertIn(12, self.processor.chapters)
        self.assertEqual(
            self.processor.chapters[12],
            ["First paragraph of chapter 12."]
        )

    def test_multiple_chapters_in_single_document(self):
        html = """
        <html>
            <body>
                <h1>CHAPTER I</h1>
                <p>Paragraph in chapter 1.</p>
                <h1>CHAPTER II</h1>
                <p>Paragraph in chapter 2.</p>
            </body>
        </html>
        """
        item = DummyItem("chapters.xhtml", html)
        self.processor.extract(item)

        self.assertEqual(list(self.processor.chapters.keys()), [1, 2])
        self.assertEqual(self.processor.chapters[1], ["Paragraph in chapter 1."])
        self.assertEqual(self.processor.chapters[2], ["Paragraph in chapter 2."])

    def test_skips_text_before_first_chapter_heading(self):
        html = """
        <html>
            <body>
                <p>Preface or intro text before any chapter.</p>
                <div>Another intro note.</div>
                <h1>CHAPTER I</h1>
                <p>Actual chapter 1 content.</p>
            </body>
        </html>
        """
        item = DummyItem("intro_and_ch1.xhtml", html)
        self.processor.extract(item)

        self.assertEqual(list(self.processor.chapters.keys()), [1])
        self.assertEqual(self.processor.chapters[1], ["Actual chapter 1 content."])

    def test_skip_container_divs(self):
        html = """
        <html>
            <body>
                <h1>CHAPTER 1</h1>
                <div class="outer">
                    <p>Paragraph nested in div.</p>
                </div>
            </body>
        </html>
        """
        item = DummyItem("ch1.xhtml", html)
        self.processor.extract(item)

        self.assertEqual(self.processor.chapters[1], ["Paragraph nested in div."])

    def test_extract_leaf_divs(self):
        html = """
        <html>
            <body>
                <h1>CHAPTER 1</h1>
                <div>Leaf div content.</div>
            </body>
        </html>
        """
        item = DummyItem("ch1.xhtml", html)
        self.processor.extract(item)

        self.assertEqual(self.processor.chapters[1], ["Leaf div content."])

    def test_text_normalization_applied(self):
        html = """
        <html>
            <body>
                <h1>CHAPTER I</h1>
                <p>\u201cCurly quotes\u201d and em\u2014dash</p>
            </body>
        </html>
        """
        item = DummyItem("ch1.xhtml", html)
        self.processor.extract(item)

        self.assertEqual(self.processor.chapters[1], ['"Curly quotes" and em - dash'])

    def test_missing_body_tag_handled_gracefully(self):
        html = "<html><head><title>No body</title></head></html>"
        item = DummyItem("nobody.xhtml", html)
        self.processor.extract(item)
        self.assertEqual(self.processor.chapters, {})

    def test_empty_and_whitespace_tags_skipped(self):
        html = """
        <html>
            <body>
                <h1>CHAPTER I</h1>
                <p></p>
                <p>   </p>
                <p>Non-empty content</p>
            </body>
        </html>
        """
        item = DummyItem("ch1.xhtml", html)
        self.processor.extract(item)
        self.assertEqual(self.processor.chapters[1], ["Non-empty content"])

    def test_end_of_gutenberg_marker_stops_processing(self):
        html = """
        <html>
            <body>
                <h1>CHAPTER I</h1>
                <p>First paragraph.</p>
                <p>*** END OF THE PROJECT GUTENBERG EBOOK TEST ***</p>
                <p>Subsequent text that should be ignored.</p>
            </body>
        </html>
        """
        item = DummyItem("ch1.xhtml", html)
        self.processor.extract(item)

        self.assertTrue(self.processor.stop_processing)
        self.assertEqual(self.processor.chapters[1], ["First paragraph."])

    def test_end_of_gutenberg_marker_variation(self):
        html = """
        <html>
            <body>
                <h1>CHAPTER I</h1>
                <p>Chapter text.</p>
                <div>*** END OF THIS PROJECT GUTENBERG EBOOK ***</div>
            </body>
        </html>
        """
        item = DummyItem("ch1.xhtml", html)
        self.processor.extract(item)

        self.assertTrue(self.processor.stop_processing)
        self.assertEqual(self.processor.chapters[1], ["Chapter text."])


class TestBestEffortProcessorProcess(unittest.TestCase):
    """Unit tests for BestEffortProcessor.process method with mock EpubBook."""

    def setUp(self):
        self.processor = BestEffortProcessor()

    def test_process_multiple_spine_items(self):
        ch1_html = "<html><body><h1>CHAPTER I</h1><p>Chapter 1 text.</p></body></html>"
        ch2_html = "<html><body><h1>CHAPTER II</h1><p>Chapter 2 text.</p></body></html>"

        ch1_item = DummyItem("ch1.xhtml", ch1_html)
        ch2_item = DummyItem("ch2.xhtml", ch2_html)

        book_mock = MagicMock()
        book_mock.spine = [
            ("id_ch1", "yes"),
            ("id_ch2", "yes"),
        ]
        item_map = {
            "id_ch1": ch1_item,
            "id_ch2": ch2_item,
        }
        book_mock.get_item_with_id.side_effect = lambda idref: item_map[idref]

        chapters = self.processor.process(book_mock)

        self.assertEqual(len(chapters), 2)
        self.assertIn(1, chapters)
        self.assertIn(2, chapters)
        self.assertEqual(chapters[1], ["Chapter 1 text."])
        self.assertEqual(chapters[2], ["Chapter 2 text."])

    def test_skips_non_linear_spine_items(self):
        linear_html = "<html><body><h1>CHAPTER I</h1><p>Linear item text.</p></body></html>"
        non_linear_html = "<html><body><h1>CHAPTER II</h1><p>Non-linear item text.</p></body></html>"

        linear_item = DummyItem("linear.xhtml", linear_html)
        non_linear_item = DummyItem("non_linear.xhtml", non_linear_html)

        book_mock = MagicMock()
        book_mock.spine = [
            ("id_linear", "yes"),
            ("id_non_linear", "no"),
        ]
        item_map = {
            "id_linear": linear_item,
            "id_non_linear": non_linear_item,
        }
        book_mock.get_item_with_id.side_effect = lambda idref: item_map[idref]

        chapters = self.processor.process(book_mock)

        self.assertEqual(len(chapters), 1)
        self.assertIn(1, chapters)
        self.assertNotIn(2, chapters)
        self.assertEqual(chapters[1], ["Linear item text."])

    def test_skips_non_document_and_none_items(self):
        ch1_html = "<html><body><h1>CHAPTER 1</h1><p>Valid doc text.</p></body></html>"
        ch1_item = DummyItem("ch1.xhtml", ch1_html, item_type=ebooklib.ITEM_DOCUMENT)
        image_item = DummyItem("cover.jpg", "", item_type=ebooklib.ITEM_IMAGE)

        book_mock = MagicMock()
        book_mock.spine = [
            ("id_ch1", "yes"),
            ("id_image", "yes"),
            ("id_none", "yes"),
        ]
        item_map = {
            "id_ch1": ch1_item,
            "id_image": image_item,
            "id_none": None,
        }
        book_mock.get_item_with_id.side_effect = lambda idref: item_map.get(idref)

        chapters = self.processor.process(book_mock)

        self.assertEqual(len(chapters), 1)
        self.assertIn(1, chapters)
        self.assertEqual(chapters[1], ["Valid doc text."])

    def test_stops_processing_subsequent_spine_items_after_end_marker(self):
        ch1_html = "<html><body><h1>CHAPTER I</h1><p>Chapter 1 text.</p></body></html>"
        end_html = "<html><body><p>*** END OF THE PROJECT GUTENBERG EBOOK ***</p></body></html>"
        ch2_html = "<html><body><h1>CHAPTER II</h1><p>Should not be processed.</p></body></html>"

        ch1_item = DummyItem("ch1.xhtml", ch1_html)
        end_item = DummyItem("end.xhtml", end_html)
        ch2_item = DummyItem("ch2.xhtml", ch2_html)

        book_mock = MagicMock()
        book_mock.spine = [
            ("id_ch1", "yes"),
            ("id_end", "yes"),
            ("id_ch2", "yes"),
        ]
        item_map = {
            "id_ch1": ch1_item,
            "id_end": end_item,
            "id_ch2": ch2_item,
        }
        book_mock.get_item_with_id.side_effect = lambda idref: item_map[idref]

        chapters = self.processor.process(book_mock)

        self.assertEqual(len(chapters), 1)
        self.assertIn(1, chapters)
        self.assertNotIn(2, chapters)
        self.assertTrue(self.processor.stop_processing)

    def test_empty_spine_returns_empty_dict(self):
        book_mock = MagicMock()
        book_mock.spine = []

        chapters = self.processor.process(book_mock)
        self.assertEqual(chapters, {})


if __name__ == "__main__":
    unittest.main()
