"""
Text extraction module supporting PDF, DOCX, and TXT resume files.
Robustly handles Gradio upload objects, SpooledTemporaryFile, dicts, and paths.
"""

import os
import io
import fitz  # PyMuPDF
import docx  # python-docx


def _read_file_bytes(file_input):
    """
    Try multiple ways to obtain file bytes and a usable filename/extension.
    Returns (bytes_or_None, filename_or_path_or_None)
    """
    # Case A: Gradio may return a dict with tmp_path or name
    if isinstance(file_input, dict):
        for key in ("tmp_path", "tmp_pathname", "tmp_file", "name"):
            candidate = file_input.get(key)
            if candidate and os.path.exists(candidate):
                with open(candidate, "rb") as f:
                    return f.read(), candidate
        # try reading value fields that may contain bytes-like data
        data = file_input.get("data")
        if isinstance(data, (bytes, bytearray)):
            return bytes(data), file_input.get("name")

    # Case B: file-like wrapper (.file attribute)
    if hasattr(file_input, "file"):
        try:
            file_input.file.seek(0)
            data = file_input.file.read()
            if isinstance(data, (bytes, bytearray)):
                return data, getattr(file_input, "name", None)
        except Exception:
            pass

    # Case C: file-like with read()
    if hasattr(file_input, "read"):
        try:
            file_input.seek(0)
            data = file_input.read()
            if isinstance(data, (bytes, bytearray)):
                return data, getattr(file_input, "name", None)
            if isinstance(data, str):
                return data.encode("utf-8", errors="ignore"), getattr(file_input, "name", None)
        except Exception:
            pass

    # Case D: attribute .name is a real path
    if hasattr(file_input, "name"):
        path = file_input.name
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return f.read(), path

    # Case E: fallback string path
    try:
        path = str(file_input)
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return f.read(), path
    except Exception:
        pass

    return None, None


def extract_text_from_resume(file_input):
    """
    Robust extraction supporting PDF, DOCX, TXT from file-like objects, dicts, or paths.
    Returns (text_or_None, error_message_or_None)
    """
    if not file_input:
        return None, "No file provided."

    b, filename = _read_file_bytes(file_input)
    if b is None:
        return None, "Could not read uploaded file (unsupported upload object or empty upload)."

    # Debug info (useful in Render logs)
    try:
        size = len(b)
    except Exception:
        size = None

    ext = (os.path.splitext(filename)[1].lower() if filename else "").strip()

    try:
        # PDF detection by extension or magic header
        if ext == ".pdf" or (len(b) >= 4 and b[:4] == b"%PDF"):
            # Open PDF from bytes stream
            doc = fitz.open(stream=b, filetype="pdf")
            pages_text = [page.get_text() for page in doc]
            text = "\n".join(pages_text).strip()
            if not text:
                return None, (
                    "PDF contains no extractable text (might be scanned images). "
                    f"(uploaded bytes={size})"
                )
            return text, None

        # DOCX detection by extension or PK zip signature
        if ext in [".docx", ".doc"] or (len(b) >= 2 and b[:2] == b"PK"):
            try:
                doc_obj = docx.Document(io.BytesIO(b))
                paragraphs = [p.text for p in doc_obj.paragraphs if p.text.strip()]
                text = "\n".join(paragraphs).strip()
                if not text:
                    return None, "DOCX file appears to be empty."
                return text, None
            except Exception:
                # Not a docx-like file, fall through
                pass

        # TXT fallback: try decode
        try:
            text = b.decode("utf-8", errors="ignore").strip()
            if text:
                return text, None
        except Exception:
            pass

        return None, "Unsupported file format or could not extract text from the uploaded file."
    except Exception as e:
        return None, f"Failed to extract text from file: {str(e)}"
