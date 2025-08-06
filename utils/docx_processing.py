# utils/docx_processing.py
import pandas as pd
from docx import Document

def process_docx_file(uploaded_file):
    """
    讀入 .docx 檔，從所有表格擷取 pandas.DataFrame 列表。
    """
    document = Document(uploaded_file)
    dfs = []
    for tbl in document.tables:
        data = []
        # 先把每個 row 轉成純文字 list
        for row in tbl.rows:
            data.append([cell.text.strip() for cell in row.cells])
        # header 為第一列，接著轉 DF
        if len(data) >= 2:
            df = pd.DataFrame(data[1:], columns=data[0])
            dfs.append(df)
    return dfs
