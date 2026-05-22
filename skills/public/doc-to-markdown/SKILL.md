---
name: doc-to-markdown
description: Convert various document formats (PDF, Word .docx, PowerPoint .pptx, images with OCR) to clean Markdown. Supports batch conversion and preserves document structure including headings, tables, lists, images, and basic formatting.
---

# Doc-to-Markdown Converter Skill

Convert documents (PDF, DOCX, PPTX, JPG/PNG) into well-structured Markdown.

## Supported Input Formats

| Format   | Engine(s)                              | Notes                                  |
|----------|----------------------------------------|----------------------------------------|
| PDF      | pdfplumber (primary), pypdfium2 (fallback), pdfminer (last resort) | Preserves text, tables; OCR via pytesseract for scanned PDFs |
| DOCX     | python-docx + mammoth                  | mammoth gives cleaner HTML->MD; python-docx handles complex formatting |
| PPTX     | python-pptx                            | Extracts slide text, notes, speaker content |
| JPG/PNG  | pytesseract (Tesseract OCR)            | Scanned documents, screenshots, image-only files |
| XLSX     | openpyxl -> markdown table              | Sheet-to-markdown-table conversion     |

## Dependencies

Python packages (all installable via pip):
- pdfplumber - PDF text/table extraction
- pypdfium2 - PDF fallback renderer
- pdfminer.six - PDF text extraction fallback
- mammoth - DOCX to HTML conversion
- python-docx - DOCX structural extraction
- python-pptx - PPTX extraction
- Pillow - Image handling
- pytesseract - OCR (requires system Tesseract)
- openpyxl - Excel parsing
- markdownify - HTML to Markdown conversion

System tools (optional, for enhanced conversion):
- tesseract-ocr - OCR engine (recommended for image/PDF OCR)
- pandoc - Universal document converter

## Core Conversion Architecture

Input File
    |
    +-- PDF ---> pdfplumber (parse) ---> text + tables ---+
    |         +-- pypdfium2 (fallback) ---> images ---> OCR ---+
    |                                                           |
    +-- DOCX ---> mammoth ---> HTML ---> markdownify ----------+
    |          +-- python-docx ---> structured elements --------+
    |                                                           |
    +-- PPTX ---> python-pptx (slide-by-slide) ----------------+
    |                                                           |
    +-- Image ---> Pillow (preprocess) ---> pytesseract --------+
    |                                                           |
    +-- XLSX ---> openpyxl ---> rows ---> MD table ------------+
                                                           |
                                                    Markdown Output

## Workflow Steps

### Step 1: Detect file type
Check file extension (.pdf, .docx, .pptx, .jpg, .jpeg, .png, .xlsx, .xls). For unknown extensions, use python-magic or file header inspection if available.

### Step 2: Extract content using the appropriate engine

#### 2a. PDF Conversion

Use pdfplumber as the primary engine:
1. Open the PDF with pdfplumber
2. For each page, extract text via extract_text()
3. Detect and extract tables via extract_tables()
4. Combine text and tables preserving reading order
5. If total extracted text < 20 chars across all pages, fall back to OCR

Scanned PDF fallback (pypdfium2 + OCR):
1. Render each page as a high-resolution image (2x scale)
2. Convert to PIL Image
3. Run Tesseract OCR on each page image
4. Collect OCR text per page

#### 2b. DOCX Conversion

Primary approach (mammoth -> HTML -> markdownify):
1. Open the .docx file with mammoth
2. Convert to HTML (preserves headings, lists, tables, formatting)
3. Use markdownify to convert HTML to Markdown
4. Set heading_style="ATX", bullets="-"

Fallback (python-docx for complex/structured docs):
1. Open the .docx file with python-docx
2. Iterate through paragraphs, checking style names
3. Map styles to markdown equivalents (Heading 1 -> #, etc.)
4. Handle tables via docx table object iteration

#### 2c. PPTX Conversion

1. Open with python-pptx
2. For each slide, add a ## Slide N header
3. Iterate through shapes on each slide
4. For text frames: extract paragraph text
5. For tables: convert to markdown table format
6. Include speaker notes if present

#### 2d. Image (JPG/PNG) OCR

1. Open image with Pillow
2. Preprocess (grayscale, contrast enhancement, thresholding)
3. Run pytesseract.image_to_string with lang='chi_sim+eng' for Chinese+English
4. Return OCR text as markdown content

#### 2e. XLSX Conversion

1. Open with openpyxl in read_only mode
2. For each sheet, convert rows to markdown table
3. First row as table header
4. Remaining rows as table data
5. Use proper markdown table separator formatting

### Step 3: Post-process and assemble Markdown

- Normalize heading levels
- Remove excessive blank lines (max 2 consecutive)
- Standardize list markers (- for unordered)
- Ensure tables have valid Markdown syntax
- Add source metadata header:

Converted from: {filename}
Conversion date: {date}
Engine: {engine_used}

### Step 4: Handle edge cases

- Password-protected PDFs: Inform user, not supported
- Corrupted files: Catch exceptions gracefully
- Empty documents: Return minimal markdown with note
- Mixed content types: Extract both text and embedded images
- Large files (>100 pages or 50MB): Process incrementally

### Step 5: Save output

Write the final Markdown to /app/backend/.deer-flow/users/c02a247c-9046-4564-b797-8a06d460d70b/threads/0862a92c-304b-4061-bd34-2d3561b318cb/user-data/outputs/ with the same base filename.

## Usage Example

User: "Convert this PDF to markdown"
Response flow:
1. Detect .pdf -> use pdfplumber
2. Extract text and tables page by page
3. If extracted text is minimal -> fall back to OCR pipeline
4. Post-process into clean Markdown
5. Save to outputs directory and present to user

## Fallback Strategy

Always attempt the primary engine first, with a clear fallback chain:

| Format | Primary | First Fallback | Last Resort |
|--------|---------|---------------|-------------|
| PDF | pdfplumber | pypdfium2 + OCR | pdfminer |
| DOCX | mammoth + markdownify | python-docx | raw text |
| PPTX | python-pptx | - | - |
| Image | pytesseract | - | - |
| XLSX | openpyxl | - | - |

## Limitations

- Complex PDF layouts (multi-column, text in images without clear scan) may lose original reading order
- Heavily formatted DOCX (complex tables, embedded fonts) may have partial fidelity loss
- PPTX speaker notes are extracted but slide transitions/animations are not preserved
- OCR quality depends on image resolution and Tesseract language packs installed
- Password-protected files are not supported
