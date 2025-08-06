# utils/docx_processing.py
import pandas as pd
from docx import Document

def process_docx_file(uploaded_file):
    doc = Document(uploaded_file)
    dfs = []
    for tbl in doc.tables:
        data = []
        for row in tbl.rows:
            data.append([cell.text.strip() for cell in row.cells])
        if len(data) < 2:
            continue
        header, *body = data
        df = pd.DataFrame(body, columns=header)
        dfs.append(df)
    return dfs
