# utils/pdf_processing.py

import io, re, streamlit as st
import pandas as pd
import pdfplumber
from pdf2image import convert_from_bytes
from PIL import Image
import easyocr

def normalize(text):
    """把任何输入转成 str，去多余空白"""
    return re.sub(r"\s+", " ", str(text) or "").strip()

def _table_to_df(raw_table):
    """
    把 pdfplumber 提取的 table(list of rows) 转成 DataFrame，去空行、补齐列数。
    """
    rows = [[normalize(c) for c in row] for row in raw_table]
    rows = [r for r in rows if any(cell for cell in r)]
    if not rows: return pd.DataFrame()
    header, *data = rows
    n = len(header)
    cleaned = []
    for row in data:
        if len(row) < n:
            row = row + [""]*(n-len(row))
        elif len(row) > n:
            row = row[:n]
        cleaned.append(row)
    df = pd.DataFrame(cleaned, columns=header)
    return df

def _is_grades_table(df):
    """
    简单检测：列数 >=3，且有“學分”“科目”类似列头。
    """
    cols = [re.sub(r"\s+","",c).lower() for c in df.columns]
    has_credit = any("學分" in c or "credit" in c for c in cols)
    has_subj   = any("科目" in c or "課程" in c or "subject" in c for c in cols)
    return has_credit and has_subj and df.shape[1]>=3

def ocr_with_easyocr(pdf_bytes):
    """
    用 EasyOCR 对每页做 OCR，回传所有行的文字列表。
    """
    reader = easyocr.Reader(['ch_tra','en'], gpu=False)
    imgs = convert_from_bytes(pdf_bytes)
    lines = []
    for img in imgs:
        result = reader.readtext(
            np.array(img),
            detail=0,           # 只取文字，不要框坐标
            paragraph=False     # 单行输出
        )
        lines.extend(result)
    return [normalize(l) for l in lines if normalize(l)]

def process_pdf_file(uploaded_file):
    """
    主流程：
    1. 先用 pdfplumber 尝试抽表格并识别成绩表
    2. 如果没抽到任何表格，就用 OCR（EasyOCR）把整份 PDF 转成行
    3. 再用行级正则把“學年度 學期 科目 學分 GPA”分离出来，拼 DataFrame 返回
    """
    raw = uploaded_file.read()
    dfs = []

    # --- 步骤 1：pdfplumber 提取表格 ---
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
        st.success(f"成功从 PDF 表格 提取到 {len(dfs)} 张成绩表")
        return dfs

    # --- 步骤 2：OCR 后备 ---
    st.info("未检测到表格，启用 OCR 后备 (EasyOCR)…")
    try:
        lines = ocr_with_easyocr(raw)
    except Exception as e:
        st.error(f"OCR 出错: {e}")
        return []

    if not lines:
        st.error("OCR 也未识别到任何文字")
        return []

    # --- 步骤 3：行级正则提取 ---
    # 合并断行：逐行累 buffer，直到匹配末尾 pattern
    end_pat = re.compile(r".+\s+\d+(\.\d+)?\s+([A-F][+\-]?|通過|抵免)$")
    merged = []
    buf = ""
    for l in lines:
        if buf:
            l = buf + " " + l
            buf = ""
        if not end_pat.match(l):
            buf = l
        else:
            merged.append(l)
    # 再用正则分组
    entry_pat = re.compile(
        r"(\d{3,4})\s*(上|下|春|夏|秋|冬)\s+(.+?)\s+(\d+(?:\.\d+)?)\s+([A-F][+\-]?|通過|抵免)$"
    )
    rows = []
    for l in merged:
        m = entry_pat.match(l)
        if not m: 
            # 可以打印日志看看哪些没匹配上
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
