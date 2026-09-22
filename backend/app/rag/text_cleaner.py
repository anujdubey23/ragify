import re

class TextCleaner:
    """
    Cleans extracted document text to improve chunking, embedding,
    and downstream retrieval quality.
    """

    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""

        # Replace null bytes and common non-printable characters
        text = text.replace("\x00", " ")
        text = text.replace("\ufeff", "")  # UTF-8 BOM
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Replace non-breaking spaces and unusual unicode spaces
        text = re.sub(r"[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000]", " ", text)

        # De-hyphenate words broken across line breaks (e.g. "retrie-\nval" -> "retrieval")
        text = re.sub(r"(\b\w+)-\n(\w+\b)", r"\1\2", text)

        # Replace 3 or more consecutive newlines with two
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Replace multiple spaces/tabs with single space (preserve intentional newlines)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        text = "\n".join(lines)

        # Final strip
        return text.strip()
