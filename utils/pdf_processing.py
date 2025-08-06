# utils/pdf_processing.py
import streamlit as st
import pandas as pd
import pdfplumber
import collections
import re

def normalize_text(cell_content):
    if cell_content is None:
        return ""
    text = str(cell_content.text) if hasattr(cell_content, "text") else str(cell_content)
    return re.sub(r'\s+', ' ', text).strip()

def make_unique_columns(columns_list):
    seen = collections.defaultdict(int)
    unique = []
    for col in columns_list:
        base = normalize_text(col) or "Column"
        name = base
        idx = seen[base]
        while name in unique:
            idx += 1
            name = f"{base}_{idx}"
        unique.append(name)
        seen[base] = idx
    return unique

def is_grades_table(df):
    # 同原本邏輯：檢查表頭與內容
    cols = [re.sub(r'\s+','',c).lower() for c in df.columns]
    if any(k in col for k in cols for k in ["學分","credit"]) and \
       any(k in col for k in cols for k in ["科目","subject"]) and \
       any(k in col for k in cols for k in ["gpa","成績"]):
        return True
    # 簡化：只要有「科目名稱」＋「學分」即可當成成績表
    return False

def process_pdf_file(uploaded_file):
    all_tables = []
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for i, page in enumerate(pdf.pages):
                settings = {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "edge_min_length": 3,
                    "join_tolerance": 5,
                    "snap_tolerance": 3,
                    "text_tolerance": 2,
                    "min_words_vertical": 1,
                    "min_words_horizontal": 1,
                }
                tables = page.extract_tables(settings)
                for tbl in tables:
                    rows = [[normalize_text(cell) for cell in row] for row in tbl]
                    # 去除全空 row
                    rows = [r for r in rows if any(r)]
                    if len(rows) < 2:
                        continue
                    header, *data = rows
                    cols = make_unique_columns(header)
                    df = pd.DataFrame(data, columns=cols)
                    if is_grades_table(df):
                        st.success(f"頁面 {i+1} 偵測到成績表格並已處理。")
                        all_tables.append(df)
    except Exception as e:
        st.error(f"PDF 處理失敗：{e}")

    return all_tables
