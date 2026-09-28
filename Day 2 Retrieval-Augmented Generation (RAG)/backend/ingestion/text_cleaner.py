import re
import unicodedata


class TextCleaner:
    """Performs text cleaning and normalization for RAG ingestion."""

    @staticmethod
    def clean(text: str) -> str:
        """Cleans and normalizes text while preserving paragraph and sentence structures.

        Args:
            text: Raw input text.

        Returns:
            Normalized clean text.
        """
        if not text:
            return ""

        # Normalize unicode (NFKC maps composite characters to standard forms)
        text = unicodedata.normalize("NFKC", text)

        # Standardize line breaks
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove null characters and non-printable control characters (keep \n and \t)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

        # Replace non-breaking spaces and unusual whitespace with standard space
        text = re.sub(r"[\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]", " ", text)

        # Collapse horizontal whitespace (multiple spaces/tabs into a single space)
        text = re.sub(r"[ \t]+", " ", text)

        # Normalize lines: strip whitespace from each line
        lines = [line.strip() for line in text.split("\n")]

        # Collapse 3 or more consecutive blank lines into at most 2 blank lines (paragraph separator)
        cleaned_lines = []
        consecutive_blanks = 0
        for line in lines:
            if not line:
                consecutive_blanks += 1
                if consecutive_blanks <= 1:
                    cleaned_lines.append("")
            else:
                consecutive_blanks = 0
                cleaned_lines.append(line)

        cleaned_text = "\n".join(cleaned_lines).strip()
        return cleaned_text
