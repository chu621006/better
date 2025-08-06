import streamlit as st
import pandas as pd
import pdfplumber
import collections
import re

def normalize_text(cell):
    if cell is None: return ""
    txt = cell.text if hasattr(cell, "text") else str(cell)
    return re.sub(r"\s+", " ", txt).strip()

def make_unique_columns(cols):
    seen = collections.Counter()
    unique = []
    for c in cols:
        base = normalize_text(c) or "Column"
        cnt = seen[base]
        name = f"{base}" if cnt == 0 else f"{base}_{cnt}"
        seen[base] += 1
        unique.append(name)
    return unique

def is_grades_table(df):
    # 檢查欄位關鍵字…（可保留你原本的判斷邏輯）
    return True  # 這裡簡化，主流程會跳過錯誤表格

def process_pdf_file(uploaded_file):
    all_tables = []
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables({
                    "vertical_strategy":"lines",
                    "horizontal_strategy":"lines",
                    "snap_tolerance":3,
                })
                for tbl in tables:
                    rows = [[normalize_text(cell) for cell in row] for row in tbl]
                    if len(rows) < 2: continue
                    df = pd.DataFrame(rows[1:], columns=make_unique_columns(rows[0]))
                    all_tables.append(df)
    except Exception as e:
        st.error(f"PDF 解析失敗：{e}")
    return all_tables
