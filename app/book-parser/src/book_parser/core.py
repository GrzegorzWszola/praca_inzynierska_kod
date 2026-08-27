from abc import ABC, abstractmethod
import unicodedata
from ebooklib.epub import EpubBook
import ebooklib
from bs4 import BeautifulSoup
import logging
import re

MATTER_TO_SKIP = {
    "titlepage", "imprint", "colophon", "uncopyright", "halftitlepage", "copyright", "dedication", "epigraph",
    "toc", "nav", "cover", "acknowledgments", "endnotes", "loi" 
}

CHAPTER_PATTERN = re.compile(
    r'\bCHAPTER\s+([IVXLCDM]+|\d+)\b',
    re.IGNORECASE
)
END_MARKER_PATTERN = re.compile(r'\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG', re.IGNORECASE)

logger = logging.getLogger()

class ProcessingCore(ABC):
    @abstractmethod
    def process(self, book: EpubBook) -> dict:
        """Process the given epub book and return a dict mapping chapter numbers to lists of text blocks."""
        pass

    def normalize(self, text: str) -> str:
        """
        Normalize extracted text for use in ML pipelines.

        Replaces typographic Unicode characters with their ASCII equivalents
        and removes invisible/zero-width characters that would pollute tokenization.
        """
        text = unicodedata.normalize("NFC", text)

        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2018", "'").replace("\u2019", "'")

        text = text.replace("\u2014", " - ").replace("\u2013", " - ")

        text = text.replace("\ufeff", "")
        text = text.replace("\u200b", "")
        text = text.replace("\u00ad", "")

        text = re.sub(r" +", " ", text)

        return text.strip()

class StandardProcessor(ProcessingCore):
    def process(self, book: EpubBook) -> dict:
        """
        Process a Standard Ebooks epub.

        Iterates over the book spine in order, skips front/back matter defined
        in MATTER_TO_SKIP, and extracts normalized text blocks chapter by chapter.
        Returns a dict of {chapter_number: [text_block, ...]}.
        """
        # Extract all elements in order of the book spine
        spine_items = [book.get_item_with_id(idref) for idref, _ in book.spine]
        items = []
        logger.info(f"Extracted {len(spine_items)} items from the book spine.")

        # Skip front/back matter (title page, copyright, TOC, etc.)
        for item in spine_items:
            item_name = item.get_name().lower()
            if any(skip_word in item_name for skip_word in MATTER_TO_SKIP):
                continue
            items.append(item)

        # Sanity check for filtered data
        logger.info(f"Filtering complete: {len(items)} chapters retained after.")

        chapters = {}
        for idx, item in enumerate(items, start=1):
            chapters[idx] = self.extract(item)

        return chapters

    def extract(self, item) -> list[str]:
        """
        Extract and normalize text blocks from a single epub spine item (chapter).

        Parses the item's HTML, collects text from <p> and leaf <div> elements,
        skips container divs that only wrap other block elements, and returns
        a list of normalized text strings — one per paragraph.
        """
        soup = BeautifulSoup(item.get_content(), features="xml")

        retrieved_text = []
        # Look for text inside of <p> or <div> blocks
        for tag in soup.find_all(["p", "div"]):
            # Skip container divs — only process leaf divs that hold actual text
            if tag.name == "div" and tag.find(["p", "div"]):
                continue
            text = tag.get_text(" ", strip=True)
            if text:
                retrieved_text.append(self.normalize(text))

        return retrieved_text

class BestEffortProcessor(ProcessingCore):
    def __init__(self):
        self.chapters = {}
        self.current_key = None
        self.stop_processing = False

    def process(self, book: EpubBook) -> dict:
        """
        Best-effort processor for non-Standard Ebooks epubs.

        Not guaranteed to produce correct results for all epub formats.
        Falls back to the StandardProcessor logic as a baseline.
        """
        warning_text = """
            You are using epub file not from standard epub and using the best effort processor and there is no guarantee
            that the transformed text will be working. For 100% sure texts check books from:\n
            https://standardebooks.org/
        """
        print(warning_text)

        # Skip non linear files in spine
        items = []
        for idref, linear in book.spine:
            if linear == "no":
                continue
            item = book.get_item_with_id(idref)
            if item is not None and item.get_type() == ebooklib.ITEM_DOCUMENT:
                items.append(item)
        logger.info(f"Extracted {len(items)} items from the book spine.")

        for item in items:
            if self.stop_processing:
                logger.info("Reached Gutenberg end marker, stopping extraction early.")
                break
            self.extract(item)

        return self.chapters

    def extract(self, item):
        soup = BeautifulSoup(item.get_content(), features="xml")
        body = soup.find("body")
        if body is None:
            return

        # Find all matching tags containing text and chapter headers
        for tag in body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "div"]):
            if tag.name == "div" and tag.find(["p", "div", "h1", "h2", "h3", "h4", "h5", "h6"]):
                continue

            text = tag.get_text(" ", strip=True)
            if not text:
                continue

            # Match fidings with pattern
            if END_MARKER_PATTERN.search(text):
                self.stop_processing = True
                return

            # Check if new chapter started
            if tag.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                match = CHAPTER_PATTERN.search(text)
                if match:
                    key_raw = match.group(1)
                    if key_raw.isdigit():
                        self.current_key = int(key_raw)
                    else:
                        self.current_key = self.roman_to_int(key_raw)
                    self.chapters[self.current_key] = []
                    continue

            # Assign text to current chapter
            if self.current_key is not None:
                self.chapters[self.current_key].append(self.normalize(text))

    def roman_to_int(self, roman: str) -> int:
        """
        Converts Roman numeral to Arabic integer.
        Raises ValueError if the string contains invalid Roman numeral characters
        or is empty.
        """
        ROMAN_VALUES = {
            'I': 1, 'V': 5, 'X': 10, 'L': 50,
            'C': 100, 'D': 500, 'M': 1000
        }

        if not roman:
            raise ValueError("Cannot convert empty string to Roman numeral")

        roman = roman.upper()
        total = 0
        prev_value = 0

        for char in reversed(roman):
            try:
                value = ROMAN_VALUES[char]
            except KeyError:
                raise ValueError(f"Invalid Roman numeral character: {char!r} in {roman!r}")

            if value < prev_value:
                total -= value
            else:
                total += value
            prev_value = value

        return total