from pathlib import Path
from ebooklib import epub
from book_parser.core import StandardProcessor, BestEffortProcessor
import logging
import json
from datetime import datetime

logger = logging.getLogger()

class BookParser:
    """
    Entry point for parsing epub books into structured JSON output.

    Detects the epub format from metadata and delegates processing
    to the appropriate processor (StandardProcessor or BestEffortProcessor).
    """

    def __init__(self, input_path, output_path):
        """
        Initialize the parser, validate the input file, and prepare the output directory.

        Args:
            input_path: Path to the input .epub file.
            output_path: Path to the directory where the output JSON will be saved.

        Raises:
            FileNotFoundError: If the input file does not exist.
            ValueError: If the epub file cannot be read.
        """
        input_path = Path(input_path)
        self.output_path = Path(output_path)

        if not input_path.is_file():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        try:
            self.book = epub.read_epub(str(input_path))
            logger.info(f"Successfully loaded EPUB file: '{input_path}'")
        except Exception as e:
            raise ValueError(f"Could not read the input file: {input_path}") from e

        # Ensure the output directory exists before processing
        self.output_path.mkdir(parents=True, exist_ok=True)

    def process_book(self):
        """
        Detect the epub format and run the appropriate processor.

        Standard Ebooks epubs are identified by their metadata identifier or publisher field.
        All other epubs fall back to BestEffortProcessor, which may not produce perfect results.
        Saves the extracted chapters to a timestamped JSON file via save_to_json().
        """
        ids = self.book.get_metadata("DC", "identifier")
        publisher = self.book.get_metadata("DC", "publisher")

        # Standard Ebooks format is guaranteed to work correctly.
        # All other epub formats are best-effort and not 100% guaranteed to parse as intended.
        if any("standardebooks.org" in v[0] for v in ids) or any("standard ebooks" in v[0] for v in publisher):
            logger.info("Standard Ebooks format recognized. Using StandardProcessor.")
            self.processor = StandardProcessor()
        else:
            logger.info("Non-standard EPUB format detected. Falling back to BestEffortProcessor.")
            self.processor = BestEffortProcessor()

        chapters = self.processor.process(self.book)
        if chapters is None:
            raise ValueError("Processing failed: processor returned None.")
        logger.info(f"Extraction complete. Successfully parsed {len(chapters)} chapters.")

        self.save_to_json(chapters)

    def save_to_json(self, chapters: dict):
        """
        Serialize extracted chapters to a JSON file.

        Each text block is assigned a globally unique id across all chapters,
        making it easy to reference individual paragraphs in the ML pipeline.
        Output filename is auto-generated from the book title and current date.

        Args:
            chapters: Dict mapping chapter numbers to lists of normalized text strings.
        """
        mapped_chapters = {}
        global_idx = 1

        for ch_num, sentences in chapters.items():
            chapter_data = []
            for sentence in sentences:
                # Each paragraph gets a unique global id for traceability in the ML pipeline
                chapter_data.append({"id": global_idx, "text": sentence})
                global_idx += 1

            mapped_chapters[f"Chapter{ch_num}"] = chapter_data

        book_name = self.book.title.lower().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        output = self.output_path / f"{book_name}_{timestamp}.json"

        with open(output, "w", encoding="utf-8") as f:
            json.dump(mapped_chapters, f, indent=4, ensure_ascii=False)

        logger.info(f"File saved to: {output}")



        



        

