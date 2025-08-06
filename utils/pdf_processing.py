# utils/pdf_processing.py

import streamlit as st
import pandas as pd
import pdfplumber
import collections
import re
from .grade_analysis import parse_credit_and_gpa, is_passing_gpa

def normalize_text(cell):
    """
    统一清洗 pdfplumber 提取的文本，去除换行、重复空白。
    """
    if cell is None:
        return ""
    txt = str(cell)
    return re.sub(r"\s+", " ", txt).strip()

def make_unique_columns(header_row):
    """
    给表头生成唯一列名列表，处理重复和空字符串。
    """
    seen = collections.Counter()
    unique_cols = []
    for raw in header_row:
        name = normalize_text(raw)
        if not name or len(name) < 2:
            base = "Column"
        else:
            base = name
        cnt = seen[base]
        col_name = f"{base}_{cnt}" if cnt > 0 else base
        unique_cols.append(col_name)
        seen[base] += 1
    return unique_cols

def is_grades_table(df):
    """
    简单判断一个 DataFrame 是否可能是成绩表：看是否有 科目/学分/GPA/学年/学期 五列之一。
    """
    cols = [re.sub(r"\s+", "", c).lower() for c in df.columns]
    has = lambda keys: any(any(k in c for k in keys) for c in cols)
    return (
        has(["科目", "course", "subject"]) and
        (has(["學分", "credit"]) or has(["gpa", "成績"])) and
        has(["學年", "year"]) and
        has(["學期", "semest"])
    )

def process_pdf_file(uploaded_file):
    """
    用 pdfplumber 提取所有表格，筛选成绩表并返回 DataFrame 列表。
    """
    all_tables = []
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables({
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 3,
                    "join_tolerance": 5,
                    "edge_min_length": 3,
                    "text_tolerance": 2
                })
                if not tables:
                    continue

                for tbl_idx, table in enumerate(tables, start=1):
                    # 清洗空行
                    rows = [[normalize_text(cell) for cell in row] for row in table]
                    rows = [r for r in rows if any(cell for cell in r)]
                    if len(rows) < 2 or len(rows[0]) < 3:
                        continue

                    header, *data = rows
                    cols = make_unique_columns(header)
                    # 对齐每行长度
                    ncol = len(cols)
                    clean = [
                        (r[:ncol] if len(r) >= ncol else r + [""]*(ncol-len(r)))
                        for r in data
                    ]
                    df = pd.DataFrame(clean, columns=cols)
                    if is_grades_table(df):
                        st.success(f"頁面 {page_num} 表格 {tbl_idx} 已識別並處理")
                        all_tables.append(df)
    except Exception as e:
        st.error(f"PDF 处理失败：{e}")
    return all_tables
