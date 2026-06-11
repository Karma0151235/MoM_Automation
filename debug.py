from docxtpl import DocxTemplate

def thorough_clean_runs(doc_obj):
    """
    Cleans up split Jinja syntax across regular paragraphs 
    AND inside all tables/cells.
    """
    # 1. Clean normal body paragraphs
    for paragraph in doc_obj.docx.paragraphs:
        _merge_paragraph_runs(paragraph)
        
    # 2. Clean paragraphs hidden inside tables (very common for MoM metrics)
    for table in doc_obj.docx.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _merge_paragraph_runs(paragraph)

def _merge_paragraph_runs(paragraph):
    """Helper to safely flatten text runs inside a single paragraph object."""
    if len(paragraph.runs) > 1:
        full_text = "".join([run.text for run in paragraph.runs])
        # Safely extract and delete trailing runs from the paragraph XML element
        for i in range(len(paragraph.runs) - 1, 0, -1):
            p_element = paragraph._p
            p_element.remove(paragraph.runs[i]._r)
        if paragraph.runs:
            paragraph.runs[0].text = full_text


