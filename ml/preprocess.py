import re

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
WIKI_RE = re.compile(r"\[\[.*?\]\]|\{\{.*?\}\}")
USER_RE = re.compile(r"\[\[User:[^\]]+\]\]", re.IGNORECASE)
NEWLINE_RE = re.compile(r"[\r\n]+")
NON_ALPHA_RE = re.compile(r"[^a-z0-9'\s]")
SPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = URL_RE.sub(" ", text)
    text = USER_RE.sub(" ", text)
    text = WIKI_RE.sub(" ", text)
    text = IP_RE.sub(" ", text)
    text = NEWLINE_RE.sub(" ", text)
    text = NON_ALPHA_RE.sub(" ", text)
    text = SPACE_RE.sub(" ", text).strip()
    return text


def validate_input(text: str, max_length: int = 5000) -> str:
    if text is None:
        raise ValueError("Comment text is required.")
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Comment text cannot be empty.")
    if len(cleaned) > max_length:
        raise ValueError(f"Comment text exceeds {max_length} characters.")
    return cleaned
