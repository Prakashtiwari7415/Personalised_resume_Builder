"""
Resume Exporter Module: Converts Markdown resumes into downloadable .md and .pdf files.
"""

import os
import re
from fpdf import FPDF
from config import EXPORT_DIR


def sanitize_for_pdf(text):
    """
    Sanitizes Unicode characters (non-breaking spaces, smart quotes, em-dashes)
    to Latin-1 compatible characters for FPDF2 rendering.
    """
    if not text:
        return ""
    
    replacements = {
        '\u202f': ' ',  # Narrow non-breaking space
        '\xa0': ' ',    # Non-breaking space
        '\u200b': '',   # Zero-width space
        '\u2013': '-',  # En-dash
        '\u2014': '-',  # Em-dash
        '\u2018': "'",  # Left single quote
        '\u2019': "'",  # Right single quote
        '\u201c': '"',  # Left double quote
        '\u201d': '"',  # Right double quote
        '\u2022': '*',  # Bullet point
        '\u2026': '...',# Ellipsis
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
        
    return text.encode('latin-1', 'replace').decode('latin-1')


class ResumePDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'AI-Optimized Professional Resume', align='R')
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


def export_markdown(markdown_text, filename="optimized_resume.md"):
    """Saves Markdown text to a downloadable file."""
    try:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        file_path = os.path.join(EXPORT_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        return file_path
    except Exception as e:
        print(f"⚠️ Warning: Failed to export Markdown file: {e}")
        return None


def export_pdf(markdown_text, filename="optimized_resume.pdf"):
    """
    Converts Markdown resume into a clean PDF document using FPDF2 with Unicode sanitization
    and layout error protection.
    """
    try:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        file_path = os.path.join(EXPORT_DIR, filename)

        pdf = ResumePDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Clean thinking tags if present and sanitize Unicode
        clean_text = re.sub(r'<think>.*?</think>', '', markdown_text, flags=re.DOTALL).strip()
        clean_text = sanitize_for_pdf(clean_text)
        lines = clean_text.splitlines()

        for line in lines:
            line_str = line.strip()
            if not line_str:
                pdf.ln(3)
                continue

            # Header 1
            if line_str.startswith("# "):
                pdf.set_font("Helvetica", "B", 15)
                pdf.set_text_color(30, 41, 59)
                pdf.multi_cell(0, 8, line_str[2:].strip())
                pdf.ln(4)

            # Header 2
            elif line_str.startswith("## "):
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(79, 70, 229)
                pdf.multi_cell(0, 7, line_str[3:].strip())
                pdf.ln(3)

            # Header 3
            elif line_str.startswith("### "):
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(51, 65, 85)
                pdf.multi_cell(0, 6, line_str[4:].strip())
                pdf.ln(2)

            # Bullet point
            elif line_str.startswith("- ") or line_str.startswith("* "):
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(51, 65, 85)
                text_body = re.sub(r'\*\*(.*?)\*\*', r'\1', line_str[2:])  # strip markdown bold
                pdf.multi_cell(0, 6, f"  * {text_body}")

            # Regular Body text
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(51, 65, 85)
                text_body = re.sub(r'\*\*(.*?)\*\*', r'\1', line_str)
                pdf.multi_cell(0, 6, text_body)

        pdf.output(file_path)
        return file_path
    except Exception as e:
        print(f"⚠️ Warning: PDF generation failed ({e}). Returning None for export.")
        return None
