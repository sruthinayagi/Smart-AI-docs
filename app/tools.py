import io
import re

import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes

def summarize_rfc(text: str, question: str | None = None) -> str:
    return f"RFC Summary:\n- {text[:200]}..."

def summarize_topic(text: str, question: str | None = None) -> str:
    topic = _extract_topic_from_question(question or "")
    sentences = re.split(r"(?<=[.!?])\s+", text)
    matches = [s.strip() for s in sentences if topic.lower() in s.lower()]
    if matches:
        summary_snippets = matches[:3]
        return (
            f"Topic summary for '{topic}':\n"
            + "\n".join(f"- {snippet}" for snippet in summary_snippets)
        )

    truncated = text[:400].strip()
    fallback = (
        "No direct sentences mentioned the topic. "
        "Here is an overview of the document instead:"
    )
    return f"{fallback}\n- {truncated}..."


def _extract_topic_from_question(question: str) -> str:
    separators = ["topic of", "topic", "about", "on", "regarding"]
    q = question.strip()
    lower_q = q.lower()
    for sep in separators:
        if sep in lower_q:
            idx = lower_q.rfind(sep)
            candidate = q[idx + len(sep):].strip(" ?.:")
            if candidate:
                return candidate
    return q or "document"


def validate_architecture(text: str, question: str | None = None) -> dict:
    findings = []
    if "monolith" in text.lower() and "event-driven" in text.lower():
        findings.append("Possible conflict: Monolith + Event-driven mentioned together.")

    return {"issues": findings or "No issues found"}

TOOLS = {
    "summarize_rfc": summarize_rfc,
    "validate_architecture": validate_architecture,
    "summarize_topic": summarize_topic,
}

def extract_text_pdfplumber(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()


def extract_text_ocr(file_bytes: bytes) -> str:
    images = convert_from_bytes(file_bytes)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text.strip()


def extract_text(file_bytes: bytes) -> str:
    # Step 1: Try pdfplumber
    text = extract_text_pdfplumber(file_bytes)

    # Step 2: If no meaningful text → OCR
    if len(text) < 50:
        text = extract_text_ocr(file_bytes)

    return text
