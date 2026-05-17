import abc
import io
import fitz  # PyMuPDF
import pymupdf4llm
from bs4 import BeautifulSoup
import re
import logging

try:
    import docx as python_docx
    _DOCX_AVAILABLE = True
except ImportError:  # pragma: no cover
    _DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Base exception for all ingestion-related errors."""
    pass

class CorruptedDataError(IngestionError):
    """Raised when input data is malformed, corrupted, or unreadable."""
    pass

class UnsupportedExtensionError(IngestionError):
    """Raised when no strategy is found for the given file extension."""
    pass

class IngestionStrategy(abc.ABC):
    """Base strategy following the Open/Closed Principle."""
    
    @abc.abstractmethod
    def ingest(self, raw_data: bytes) -> str:
        """Process raw bytes and return cleaned markdown/text string."""
        pass

class PDFIngestionStrategy(IngestionStrategy):
    def ingest(self, raw_data: bytes) -> str:
        return ContractIngestionEngine.parse_pdf_to_markdown(raw_data)

class HTMLIngestionStrategy(IngestionStrategy):
    def ingest(self, raw_data: bytes) -> str:
        try:
            # Handle potentially malformed bytes with fallback
            html_content = raw_data.decode('utf-8', errors='replace')
            return ContractIngestionEngine.clean_extension_html(html_content)
        except Exception as e:
            logger.error(f"Failed to decode HTML bytes: {str(e)}")
            raise CorruptedDataError(f"Failed to decode HTML: {str(e)}")

class PlainTextIngestionStrategy(IngestionStrategy):
    def ingest(self, raw_data: bytes) -> str:
        try:
            text = raw_data.decode('utf-8', errors='replace')
            return ContractIngestionEngine._clean_text(text)
        except Exception as e:
            logger.error(f"Failed to decode plain-text bytes: {str(e)}")
            raise CorruptedDataError(f"Failed to decode plain text: {str(e)}")


class DOCXIngestionStrategy(IngestionStrategy):
    """
    Extracts plain text from DOCX bytes using python-docx.
    Falls back to a raw-string binary scan when the library is unavailable.
    Produces a clean, LLM-ready Markdown string.
    """

    def ingest(self, raw_data: bytes) -> str:
        if not raw_data:
            raise CorruptedDataError("Received empty buffer for DOCX parsing.")

        if _DOCX_AVAILABLE:
            return self._parse_with_python_docx(raw_data)
        else:
            # Ultra-lightweight fallback: extract printable ASCII runs from the ZIP
            return self._binary_text_fallback(raw_data)

    @staticmethod
    def _parse_with_python_docx(raw_data: bytes) -> str:
        try:
            document = python_docx.Document(io.BytesIO(raw_data))
        except Exception as exc:
            raise CorruptedDataError(
                f"DOCX data is corrupted or not a valid .docx file: {exc}"
            )

        lines: list[str] = []
        for para in document.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            # Promote heading styles to Markdown heading syntax
            style = para.style.name if para.style else ""
            if style.startswith("Heading 1"):
                lines.append(f"# {text}")
            elif style.startswith("Heading 2"):
                lines.append(f"## {text}")
            elif style.startswith("Heading 3"):
                lines.append(f"### {text}")
            else:
                lines.append(text)

        result = "\n".join(lines)
        return ContractIngestionEngine._clean_text(result)

    @staticmethod
    def _binary_text_fallback(raw_data: bytes) -> str:
        """Scans binary payload for printable ASCII runs ≥ 20 chars as a last resort."""
        import re as _re
        text = raw_data.decode("latin-1", errors="ignore")
        runs = _re.findall(r'[\x20-\x7e]{20,}', text)
        result = "\n".join(runs)
        return ContractIngestionEngine._clean_text(result)


class ContractIngestionEngine:
    """
    Extensible engine to parse different file types into standard text.
    Implements the Open/Closed Principle so new ingestion formats can 
    be added without altering existing code.
    """
    
    def __init__(self):
        self._strategies = {}
        # Pre-register common strategies
        self.register_strategy('pdf',  PDFIngestionStrategy())
        self.register_strategy('html', HTMLIngestionStrategy())
        self.register_strategy('docx', DOCXIngestionStrategy())
        # Plain-text variants: 'text', 'txt', and 'plain' all route here
        _text_strategy = PlainTextIngestionStrategy()
        self.register_strategy('text', _text_strategy)
        self.register_strategy('txt', _text_strategy)
        self.register_strategy('plain', _text_strategy)

    def register_strategy(self, extension: str, strategy: IngestionStrategy) -> None:
        """Register a new ingestion strategy for a given file extension."""
        if not extension or not isinstance(extension, str):
            raise ValueError("Extension must be a valid string.")
        self._strategies[extension.lower()] = strategy

    def process_file(self, extension: str, file_bytes: bytes) -> str:
        """Process a file based on its extension using the registered strategy."""
        strategy = self._strategies.get(extension.lower())
        if not strategy:
            raise UnsupportedExtensionError(f"No ingestion strategy registered for '{extension}'")
        
        try:
            return strategy.ingest(file_bytes)
        except IngestionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during ingestion of {extension}: {str(e)}")
            raise IngestionError(f"Failed to process {extension}: {str(e)}")

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Applies Fabric pattern text structuring and clean-up mechanics.
        Handles malformed strings, trace characters, and corrupted input buffers.
        """
        if not text:
            return ""
        
        try:
            # Remove null bytes and corrupted trace characters
            text = text.replace('\x00', '')
            
            # Remove unwanted control characters (except newline and tab)
            text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
            
            # Clean up strange line breaks: replace multiple blank lines with max two
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            # Strip trailing/leading spaces on each line to fix weird breaks
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join(lines)
            
            return text.strip()
        except Exception as e:
            logger.warning(f"Error during text cleanup: {e}")
            # Fallback gracefully
            return text

    @classmethod
    def parse_pdf_to_markdown(cls, file_bytes: bytes) -> str:
        """
        Parses PDF bytes to Markdown using pymupdf4llm.
        Handles layouts, headers, and multi-column document grids rapidly.
        """
        if not file_bytes:
            raise CorruptedDataError("Received empty buffer for PDF parsing.")
        
        try:
            doc = fitz.Document(stream=file_bytes, filetype="pdf")
            raw_markdown = pymupdf4llm.to_markdown(doc)
            return cls._clean_text(raw_markdown)
        except fitz.FileDataError as e:
            logger.error(f"PDF file data error: {str(e)}")
            raise CorruptedDataError("The provided PDF data is corrupted or invalid.")
        except Exception as e:
            logger.error(f"PDF parsing error: {str(e)}")
            raise IngestionError(f"An error occurred while parsing the PDF: {str(e)}")

    @classmethod
    def clean_extension_html(cls, raw_html: str) -> str:
        """
        Isolates inner-text content strings passed dynamically from Chrome Extension DOM scraping.
        """
        if not raw_html:
            raise CorruptedDataError("Received empty string for HTML cleaning.")
            
        try:
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Remove script and style elements as they are not content
            for script_or_style in soup(['script', 'style', 'noscript', 'meta', 'link']):
                script_or_style.decompose()
                
            # Extract text
            text = soup.get_text(separator='\n', strip=True)
            
            # Apply general cleanup mechanics
            return cls._clean_text(text)
        except Exception as e:
            logger.error(f"HTML parsing error: {str(e)}")
            raise CorruptedDataError(f"Failed to parse and clean HTML data: {str(e)}")
