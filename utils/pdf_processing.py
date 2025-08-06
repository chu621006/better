# utils/pdf_processing.py

import io
import re
import streamlit as st
import pandas as pd
import pdfplumber
import fitz                 # PyMuPDF
from PIL import Image
import easyocr

def normalize(text):
    """把任何输入转成 str，去多余空白"""
    return re.sub(r"\s+", " ", str(text) or "").strip()

def _table_to_df(raw_table):
    rows = [[normalize(c) for c in row] for row in raw_table]
    rows = [r for r in rows if any(cell for cell in r)]
    if not rows:
        return pd.DataFrame()
    header, *data = rows
    n = len(header)
    cleaned = []
    for row in data:
        if len(row) < n:
            row = row + [""] * (n - len(row))
        elif len(row) > n:
            row = row[:n]
        cleaned.append(row)
    return pd.DataFrame(cleaned, columns=header)

def _is_grades_table(df):
    cols = [re.sub(r"\s+", "", c).lower() for c in df.columns]
    has_credit = any("學分" in c or "credit" in c for c in cols)
    has_subj   = any("科目" in c or "課程" in c or "subject" in c for c in cols)
    return has_credit and has_subj and df.shape[1] >= 3

def _pdf_to_images_via_fitz(pdf_bytes):
    """
    使用 PyMuPDF 渲染每一页为 PIL.Image，不依赖 poppler。
    """
    images = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x 放大提高 OCR 识别率
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def ocr_with_easyocr(pdf_bytes):
    reader = easyocr.Reader(['ch_tra','en'], gpu=False)
    images = _pdf_to_images_via_fitz(pdf_bytes)
    lines = []
    for img in images:
        result = reader.readtext(
            # easyocr 接受 numpy array
            __import__('numpy').array(img),
            detail=0,
            paragraph=False
        )
        lines.extend(result)
    return [normalize(l) for l in lines if normalize(l)]

def process_pdf_file(uploaded_file):
    raw = uploaded_file.read()
    dfs = []

    # 1. 先试 pdfplumber 表格
    try:
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for p in pdf.pages:
                tables = p.extract_tables({
                    "vertical_strategy":"lines",
                    "horizontal_strategy":"lines",
                    "snap_tolerance":3,
                    "join_tolerance":5,
                    "edge_min_length":3,
                    "text_tolerance":2
                })
                for tbl in tables:
                    df = _table_to_df(tbl)
                    if _is_grades_table(df):
                        dfs.append(df)
    except Exception as e:
        st.warning(f"pdfplumber 失败: {e}")

    if dfs:
        st.success(f"成功从 PDF 表格提取到 {len(dfs)} 张成绩表")
        return dfs

    # 2. 再用 OCR 后备
    st.info("未检测到表格，启用 OCR 后备 (EasyOCR)…")
    try:
        lines = ocr_with_easyocr(raw)
    except Exception as e:
        st.error(f"OCR 出错: {e}")
        return []

    if not lines:
        st.error("OCR 也未识别到任何文字")
        return []

    # 3. 行级正则合并 & 提取
    end_pat = re.compile(r".+\s+\d+(\.\d+)?\s+([A-F][+\-]?|通過|抵免)$")
    merged, buf = [], ""
    for l in lines:
        if buf:
            l = buf + " " + l
            buf = ""
        if not end_pat.match(l):
            buf = l
        else:
            merged.append(l)

    entry_pat = re.compile(
        r"(\d{3,4})\s*(上|下|春|夏|秋|冬)\s+(.+?)\s+(\d+(?:\.\d+)?)\s+([A-F][+\-]?|通過|抵免)$"
    )
    rows = []
    for l in merged:
        m = entry_pat.match(l)
        if not m:
            st.debug(f"OCR 未匹配: {l}")
            continue
        y, sem, subj, cr, gpa = m.groups()
        rows.append({
            "學年度": y,
            "學期": sem,
            "科目名稱": normalize(subj),
            "學分": float(cr),
            "GPA": gpa
        })

    if not rows:
        st.warning("OCR 匹配后仍无有效课程行")
        return []

    df_final = pd.DataFrame(rows)
    st.success(f"OCR 共解析到 {len(rows)} 门课程")
    return [df_final]
