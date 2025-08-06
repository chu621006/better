# utils/grade_analysis.py
import pandas as pd
import re
from .pdf_processing import normalize_text

def is_passing_gpa(gpa_str):
    # ...（原本函式不變）
    g = normalize_text(gpa_str).upper()
    failing = ["D","D-","E","F","X","不通過","未通過"]
    if not g:
        return False
    if g in ["通過","抵免","PASS","EXEMPT"]:
        return True
    if g in failing:
        return False
    if re.match(r'^[A-C][+\-]?$', g):
        return True
    if g.replace('.','',1).isdigit():
        return float(g) >= 60.0
    return False

def parse_credit_and_gpa(text):
    # ...（原本函式不變）
    txt = normalize_text(text)
    # 處理通過、數字、A-F 等
    if txt.lower() in ["通過","抵免","pass","exempt"]:
        return 0.0, txt
    m1 = re.match(r'([A-Fa-f][+\-]?)\s*(\d+(\.\d+)?)', txt)
    if m1:
        return float(m1.group(2)), m1.group(1).upper()
    m2 = re.match(r'(\d+(\.\d+)?)\s*([A-Fa-f][+\-]?)', txt)
    if m2:
        return float(m2.group(1)), m2.group(3).upper()
    num = re.search(r'(\d+(\.\d+)?)', txt)
    if num:
        return float(num.group(1)), ""
    let = re.search(r'([A-Fa-f][+\-]?)', txt)
    if let:
        return 0.0, let.group(1).upper()
    return 0.0, ""

def calculate_total_credits(df_list):
    total = 0.0
    passed = []
    failed = []
    for idx, df in enumerate(df_list, start=1):
        # 嘗試自動找到關鍵欄位
        cols = [re.sub(r'\s+','',c).lower() for c in df.columns]
        try:
            subj_col = next(c for c in df.columns if "科目" in re.sub(r'\s+','',c))
            credit_col = next(c for c in df.columns if "學分" in re.sub(r'\s+','',c))
            gpa_col = next(c for c in df.columns if "gpa" in c.lower() or "成績" in c)
        except StopIteration:
            continue

        for _, row in df.iterrows():
            s = normalize_text(row[subj_col])
            cred_txt = normalize_text(row[credit_col])
            gpa_txt  = normalize_text(row[gpa_col])
            cred, gpa = parse_credit_and_gpa(cred_txt), parse_credit_and_gpa(gpa_txt)
            credit = cred[0] or gpa[0]
            grade  = gpa[1] or cred[1]

            if grade and not is_passing_gpa(grade):
                failed.append({"科目名稱": s, "學分": credit, "GPA": grade})
            else:
                total += credit
                passed.append({"科目名稱": s, "學分": credit, "GPA": grade})

    return total, passed, failed
