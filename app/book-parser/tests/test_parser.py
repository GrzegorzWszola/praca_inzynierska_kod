import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json
from book_parser.parser import BookParser
from book_parser.core import StandardProcessor, BestEffortProcessor


class TestBookParser(unittest.TestCase):
    """Unit tests for BookParser class."""

    def test_init_file_not_found_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            BookParser("/path/does/not/exist.epub", "/tmp/output")

    @patch("book_parser.parser.epub.read_epub")
    def test_init_invalid_epub_raises_value_error(self, mock_read_epub):
        mock_read_epub.side_effect = Exception("Corrupted epub")
        with tempfile.NamedTemporaryFile(suffix=".epub") as temp_epub:
            with self.assertRaises(ValueError) as ctx:
                BookParser(temp_epub.name, "/tmp/output")
            self.assertIn("Could not read the input file", str(ctx.exception))

    @patch("book_parser.parser.epub.read_epub")
    def test_process_book_uses_standard_processor_for_standard_ebooks_identifier(self, mock_read_epub):
        mock_book = MagicMock()
        mock_book.title = "Sample Book"
        mock_book.get_metadata.side_effect = lambda schema, name: (
            [("https://standardebooks.org/ebooks/author/title", {})]
            if name == "identifier" else []
        )
        mock_read_epub.return_value = mock_book

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_epub = Path(tmp_dir) / "test.epub"
            temp_epub.touch()

            parser = BookParser(str(temp_epub), tmp_dir)
            with patch.object(StandardProcessor, "process", return_value={1: ["Paragraph 1"]}) as mock_proc:
                parser.process_book()
                self.assertIsInstance(parser.processor, StandardProcessor)
                mock_proc.assert_called_once_with(mock_book)

    @patch("book_parser.parser.epub.read_epub")
    def test_process_book_uses_best_effort_processor_for_non_standard_epub(self, mock_read_epub):
        mock_book = MagicMock()
        mock_book.title = "Gutenberg Book"
        mock_book.get_metadata.side_effect = lambda schema, name: []
        mock_read_epub.return_value = mock_book

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_epub = Path(tmp_dir) / "test.epub"
            temp_epub.touch()

            parser = BookParser(str(temp_epub), tmp_dir)
            with patch.object(BestEffortProcessor, "process", return_value={1: ["Paragraph 1"]}) as mock_proc:
                parser.process_book()
                self.assertIsInstance(parser.processor, BestEffortProcessor)
                mock_proc.assert_called_once_with(mock_book)

    @patch("book_parser.parser.epub.read_epub")
    def test_save_to_json_creates_structured_output_with_continuous_ids(self, mock_read_epub):
        mock_book = MagicMock()
        mock_book.title = "My Test Book"
        mock_book.get_metadata.return_value = []
        mock_read_epub.return_value = mock_book

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_epub = Path(tmp_dir) / "test.epub"
            temp_epub.touch()

            parser = BookParser(str(temp_epub), tmp_dir)
            chapters = {
                1: ["First sentence of chapter 1.", "Second sentence of chapter 1."],
                2: ["First sentence of chapter 2."]
            }
            parser.save_to_json(chapters)

            json_files = list(Path(tmp_dir).glob("my_test_book_*.json"))
            self.assertEqual(len(json_files), 1)

            with open(json_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(list(data.keys()), ["Chapter1", "Chapter2"])
            self.assertEqual(data["Chapter1"], [
                {"id": 1, "text": "First sentence of chapter 1."},
                {"id": 2, "text": "Second sentence of chapter 1."}
            ])
            self.assertEqual(data["Chapter2"], [
                {"id": 3, "text": "First sentence of chapter 2."}
            ])


if __name__ == "__main__":
    unittest.main()
