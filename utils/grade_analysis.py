# utils/grade_analysis.py

import pandas as pd
import re
from .pdf_processing import normalize as normalize_text

def is_passing_gpa(gpa_str):
    """
    判斷給定的 GPA 字串是否為通過成績。
    """
    gpa_clean = normalize_text(gpa_str).upper()
    failing_grades = ["D", "D-", "E", "F", "X", "不通過", "未通過", "不及格"]
    if not gpa_clean:
        return False
    if gpa_clean in ["通過", "抵免", "PASS", "EXEMPT"]:
        return True
    if gpa_clean in failing_grades:
        return False
    if re.match(r'^[A-C][+\-]?$', gpa_clean):
        return True
    if gpa_clean.replace('.', '', 1).isdigit():
        try:
            return float(gpa_clean) >= 60.0
        except ValueError:
            pass
    return False

def parse_credit_and_gpa(text):
    """
    從單元格文本中解析學分和 GPA。
    返回 (學分, GPA)。
    """
    text_clean = normalize_text(text)
    # 通過 / 抵免
    if text_clean.lower() in ["通過", "抵免", "pass", "exempt"]:
        return 0.0, text_clean

    # GPA + 學分
    m = re.match(r'([A-Fa-f][+\-]?)\s*(\d+(\.\d+)?)', text_clean)
    if m:
        return float(m.group(2)), m.group(1).upper()

    # 學分 + GPA
    m = re.match(r'(\d+(\.\d+)?)\s*([A-Fa-f][+\-]?)', text_clean)
    if m:
        return float(m.group(1)), m.group(3).upper()

    # 單純學分
    m = re.search(r'(\d+(\.\d+)?)', text_clean)
    if m:
        return float(m.group(1)), ""

    # 單純 GPA
    m = re.search(r'([A-Fa-f][+\-]?)', text_clean)
    if m:
        return 0.0, m.group(1).upper()

    return 0.0, ""

def calculate_total_credits(df_list):
    """
    從提取的 DataFrames 列表中計算總學分。
    返回: (total_credits, calculated_courses, failed_courses)
    """
    total_credits = 0.0
    calculated_courses = []
    failed_courses = []

    for df_idx, df in enumerate(df_list):
        # 跳過不合條件的 DataFrame
        if df.empty or df.shape[1] < 3:
            continue

        # 嘗試自動找到關鍵欄位
        cols_norm = {re.sub(r'\s+', '', c).lower(): c for c in df.columns}
        # 學分
        for k in ["學分", "credit", "credits", "學分數"]:
            if k in cols_norm:
                credit_col = cols_norm[k]
                break
        else:
            credit_col = None

        # 科目名稱
        for k in ["科目名稱", "課程名稱", "subject", "coursename"]:
            if k in cols_norm:
                subj_col = cols_norm[k]
                break
        else:
            subj_col = None

        # GPA
        for k in ["gpa", "成績", "grade"]:
            if k in cols_norm:
                gpa_col = cols_norm[k]
                break
        else:
            gpa_col = None

        # 如果沒找到必要欄位就跳過
        if not credit_col or not subj_col or not gpa_col:
            continue

        # 逐行計算
        for _, row in df.iterrows():
            subj_raw = normalize_text(row.get(subj_col, ""))
            cred_txt = normalize_text(row.get(credit_col, ""))
            gpa_txt  = normalize_text(row.get(gpa_col, ""))

            cred, gpa = parse_credit_and_gpa(cred_txt)
            # 如果 credit 讀不到，嘗試從 GPA 欄位補學分
            if cred == 0:
                c2, _ = parse_credit_and_gpa(gpa_txt)
                if c2 > 0:
                    cred = c2

            # 判定是否通過
            passing = is_passing_gpa(gpa_txt) or cred > 0
            if not passing:
                # 未通過才歸入 failed
                failed_courses.append({
                    "學年度": normalize_text(row.get(cols_norm.get("學年",""), "")),
                    "學期": normalize_text(row.get(cols_norm.get("學期",""), "")),
                    "科目名稱": subj_raw or "未知科目",
                    "學分": cred,
                    "GPA": gpa_txt,
                    "來源表格": df_idx + 1
                })
            else:
                # 通過，才計學分
                total_credits += cred
                calculated_courses.append({
                    "學年度": normalize_text(row.get(cols_norm.get("學年",""), "")),
                    "學期": normalize_text(row.get(cols_norm.get("學期",""), "")),
                    "科目名稱": subj_raw or "未知科目",
                    "學分": cred,
                    "GPA": gpa_txt,
                    "來源表格": df_idx + 1
                })

    return total_credits, calculated_courses, failed_courses
