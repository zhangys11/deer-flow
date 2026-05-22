#!/usr/bin/env python3
"""
doc-to-markdown Converter Script
Converts PDF, DOCX, PPTX, JPG/PNG, XLSX to Markdown.
"""

import os
import sys
import re
import traceback
from pathlib import Path
from datetime import datetime


def convert_pdf_pdfplumber(filepath):
    """Convert PDF to Markdown using pdfplumber (primary engine)."""
    import pdfplumber
    md_parts = [
        f"<!-- Converted from: {Path(filepath).name} -->",
        f"<!-- Conversion date: {datetime.now().isoformat()} -->",
        f"<!-- Engine: pdfplumber -->\n",
    ]
    total_text = 0

    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            md_parts.append(f"\n## Page {page_num}\n")
            text = page.extract_text() or ""
            total_text += len(text)
            if text.strip():
                md_parts.append(f"{text.strip()}\n")
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 0:
                    md_parts.append(f"\n{_table_to_markdown(table)}\n")

    content = "\n".join(md_parts)
    if total_text < 20:
        return None
    return content


def convert_pdf_ocr(filepath):
    """Convert scanned PDF via pypdfium2 + pytesseract."""
    import pypdfium2 as pdfium
    from PIL import Image
    import pytesseract

    md_parts = [
        f"<!-- Converted from: {Path(filepath).name} -->",
        f"<!-- Conversion date: {datetime.now().isoformat()} -->",
        f"<!-- Engine: pypdfium2 + pytesseract (OCR) -->\n",
    ]
    pdf = pdfium.PdfDocument(filepath)
    for page_index in range(len(pdf)):
        page = pdf[page_index]
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()
        text = pytesseract.image_to_string(pil_image, lang="chi_sim+eng")
        page_num = page_index + 1
        md_parts.append(f"\n## Page {page_num}\n")
        if text.strip():
            md_parts.append(f"{text.strip()}\n")
    pdf.close()
    return "\n".join(md_parts)


def convert_pdf_miner(filepath):
    """Fallback PDF using pdfminer.six."""
    from pdfminer.high_level import extract_text
    text = extract_text(filepath)
    md_parts = [
        f"<!-- Converted from: {Path(filepath).name} -->",
        f"<!-- Conversion date: {datetime.now().isoformat()} -->",
        f"<!-- Engine: pdfminer (fallback) -->\n",
    ]
    if text.strip():
        md_parts.append(text)
    return "\n".join(md_parts)

def convert_docx_mammoth(filepath):
    """Convert DOCX to Markdown using mammoth + markdownify."""
    import mammoth
    from markdownify import markdownify as md

    with open(filepath, "rb") as f:
        result = mammoth.convert_to_html(f)
        html = result.value
        markdown_text = md(html, heading_style="ATX", bullets="-")

    header = [
        f"<!-- Converted from: {Path(filepath).name} -->",
        f"<!-- Conversion date: {datetime.now().isoformat()} -->",
        f"<!-- Engine: mammoth -->\n",
    ]
    return "\n".join(header) + "\n" + markdown_text


def convert_docx_python_docx(filepath):
    """Fallback DOCX using python-docx."""
    from docx import Document

    doc = Document(filepath)
    md_parts = [
        f"<!-- Converted from: {Path(filepath).name} -->",
        f"<!-- Conversion date: {datetime.now().isoformat()} -->",
        f"<!-- Engine: python-docx (fallback) -->\n",
    ]
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            md_parts.append("")
            continue
        style_name = para.style.name if para.style else ""
        if style_name.startswith("Heading 1"):
            md_parts.append(f"# {text}")
        elif style_name.startswith("Heading 2"):
            md_parts.append(f"## {text}")
        elif style_name.startswith("Heading 3"):
            md_parts.append(f"### {text}")
        elif style_name.startswith("Heading"):
            level = style_name.replace("Heading ", "")
            if level.isdigit():
                md_parts.append(f"{'#' * int(level)} {text}")
            else:
                md_parts.append(text)
        elif style_name.startswith("List"):
            md_parts.append(f"- {text}")
        else:
            md_parts.append(text)

    for table in doc.tables:
        md_parts.append(f"\n{_docx_table_to_markdown(table)}\n")
    return "\n".join(md_parts)


def convert_pptx(filepath):
    """Convert PPTX to Markdown using python-pptx."""
    from pptx import Presentation

    prs = Presentation(filepath)
    md_parts = [
        f"<!-- Converted from: {Path(filepath).name} -->",
        f"<!-- Conversion date: {datetime.now().isoformat()} -->",
        f"<!-- Engine: python-pptx -->\n",
    ]
    for i, slide in enumerate(prs.slides):
        slide_num = i + 1
        md_parts.append(f"\n## Slide {slide_num}\n")
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        md_parts.append(f"{text}\n")
            if shape.has_table:
                table = shape.table
                rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
                md_parts.append(f"\n{_table_to_markdown(rows)}\n")
    return "\n".join(md_parts)


def convert_image(filepath):
    """Convert image to Markdown via pytesseract OCR."""
    from PIL import Image
    import pytesseract

    img = Image.open(filepath)
    img = img.convert("L")
    text = pytesseract.image_to_string(img, lang="chi_sim+eng")

    md_parts = [
        f"<!-- Converted from: {Path(filepath).name} -->",
        f"<!-- Conversion date: {datetime.now().isoformat()} -->",
        f"<!-- Engine: pytesseract OCR -->\n",
    ]
    if text.strip():
        md_parts.append(text.strip())
    return "\n".join(md_parts)


def convert_xlsx(filepath):
    """Convert XLSX to Markdown tables via openpyxl."""
    import openpyxl

    wb = openpyxl.load_workbook(filepath, read_only=True)
    md_parts = [
        f"<!-- Converted from: {Path(filepath).name} -->",
        f"<!-- Conversion date: {datetime.now().isoformat()} -->",
        f"<!-- Engine: openpyxl -->\n",
    ]
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        md_parts.append(f"\n## Sheet: {sheet_name}\n")
        rows_data = []
        for row in ws.iter_rows(values_only=True):
            row_values = [str(cell) if cell is not None else "" for cell in row]
            rows_data.append(row_values)
        if rows_data:
            md_parts.append(_table_to_markdown(rows_data))
    wb.close()
    return "\n".join(md_parts)

def _table_to_markdown(rows):
    """Convert list of lists to Markdown table."""
    if not rows or len(rows) == 0:
        return ""

    max_cols = max(len(row) for row in rows)
    normalized = []
    for row in rows:
        r = list(row)
        while len(r) < max_cols:
            r.append("")
        normalized.append(r)

    header = normalized[0]
    md_lines = ["| " + " | ".join(header) + " |"]
    separators = ["---"] * max_cols
    md_lines.append("| " + " | ".join(separators) + " |")
    for row in normalized[1:]:
        md_lines.append("| " + " | ".join(row) + " |")
    return "\n".join(md_lines)


def _docx_table_to_markdown(table):
    """Convert python-docx table to Markdown."""
    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    return _table_to_markdown(rows)


def convert_to_markdown(filepath, output_dir=None):
    """
    Main entry point: convert a file to Markdown.

    Args:
        filepath: Path to input file (PDF, DOCX, PPTX, JPG, PNG, XLSX)
        output_dir: Optional output directory (default: /app/backend/.deer-flow/users/c02a247c-9046-4564-b797-8a06d460d70b/threads/0862a92c-304b-4061-bd34-2d3561b318cb/user-data/outputs)

    Returns:
        Path to output Markdown file, or None on failure.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        return None

    suffix = filepath.suffix.lower()
    basename = filepath.stem

    if output_dir is None:
        output_dir = Path("/app/backend/.deer-flow/users/c02a247c-9046-4564-b797-8a06d460d70b/threads/0862a92c-304b-4061-bd34-2d3561b318cb/user-data/outputs")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{basename}.md"

    print(f"Converting: {filepath}")
    print(f"Format: {suffix}")

    try:
        if suffix == ".pdf":
            markdown_text = convert_pdf_pdfplumber(str(filepath))
            if markdown_text is None:
                print("Low text content detected, trying OCR...")
                try:
                    markdown_text = convert_pdf_ocr(str(filepath))
                except Exception:
                    print("OCR fallback failed, trying pdfminer...")
                    markdown_text = convert_pdf_miner(str(filepath))

        elif suffix == ".docx":
            try:
                markdown_text = convert_docx_mammoth(str(filepath))
            except Exception:
                print("mammoth failed, falling back to python-docx...")
                markdown_text = convert_docx_python_docx(str(filepath))

        elif suffix == ".pptx":
            markdown_text = convert_pptx(str(filepath))

        elif suffix in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"):
            markdown_text = convert_image(str(filepath))

        elif suffix in (".xlsx", ".xls"):
            markdown_text = convert_xlsx(str(filepath))

        else:
            print(f"Unsupported file format: {suffix}")
            return None

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        char_count = len(markdown_text)
        print(f"\nSuccessfully converted to: {output_path}")
        print(f"Output size: {char_count} characters")
        return output_path

    except ImportError as e:
        print(f"Missing dependency: {e}")
        return None
    except Exception as e:
        print(f"Conversion failed: {e}")
        traceback.print_exc()
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert.py <filepath> [output-directory]")
        print("Supported: .pdf .docx .pptx .jpg/.jpeg/.png .xlsx/.xls")
        sys.exit(1)
    filepath = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    result = convert_to_markdown(filepath, output_dir)
    if result:
        print(f"\nOutput file: {result}")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
