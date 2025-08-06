# utils/grade_analysis.py

import re

def normalize_text(cell):
    """
    将任意类型的单元格内容转换为字符串，
    并去除多余空白（包括换行），返回干净的文本。
    """
    if cell is None:
        return ""
    text = str(cell)
    return re.sub(r'\s+', ' ', text).strip()

def is_passing_gpa(gpa_str):
    """
    判断一个 GPA 字符串是否为及格。
    支持字母成绩（A~F+/-）、通过/抵免标识，以及数字分数。
    """
    gpa = normalize_text(gpa_str).upper()
    if not gpa:
        return False

    # 明确的及格标识
    if gpa in {"通過", "抵免", "PASS", "EXEMPT"}:
        return True

    # 明确的不及格标识
    if gpa in {"D", "D-", "E", "F", "X", "不通過", "未通過", "不及格"}:
        return False

    # A/B/C 及其 +/- 视为及格
    if re.fullmatch(r"[A-C][+-]?", gpa):
        return True

    # 数字分数，假设 >= 60 及格
    if gpa.replace('.', '', 1).isdigit():
        try:
            return float(gpa) >= 60.0
        except ValueError:
            pass

    return False

def parse_credit_and_gpa(cell_text):
    """
    从一个单元格文本（可能同时含学分和 GPA，也可能只有一者）中解析学分和 GPA。
    返回 (credit: float, gpa: str)。
    """
    txt = normalize_text(cell_text)

    # 如果是通过/抵免
    if txt.upper() in {"通過", "抵免", "PASS", "EXEMPT"}:
        return 0.0, txt

    # 形如 "A 2" 或 "A- 3"
    m = re.match(r"^([A-Fa-f][+-]?)[\s,／/]*(\d+(\.\d+)?)$", txt)
    if m:
        return float(m.group(2)), m.group(1).upper()

    # 形如 "2 A" 或 "3.0 B+"
    m = re.match(r"^(\d+(\.\d+)?)[\s,／/]*([A-Fa-f][+-]?)$", txt)
    if m:
        return float(m.group(1)), m.group(3).upper()

    # 只有学分
    m = re.fullmatch(r"(\d+(\.\d+)?)", txt)
    if m:
        return float(m.group(1)), ""

    # 只有 GPA
    m = re.fullmatch(r"([A-Fa-f][+-]?|通過|抵免|PASS|EXEMPT)", txt, re.IGNORECASE)
    if m:
        return 0.0, m.group(1).upper()

    return 0.0, ""

def calculate_total_credits(df_list):
    """
    从多个 pandas.DataFrame（每个都是一个成绩表格）中，
    识别并累加及格课程的学分，返回 (total_credits, passed_courses, failed_courses)。
    自动合并跨行的课程名称。
    """
    total_credits = 0.0
    passed_courses = []
    failed_courses = []

    # 可能的列名关键词，用于在不同格式的表格中定位
    credit_keys = ["學分", "credits", "credit"]
    gpa_keys    = ["GPA", "成績", "grade"]
    subject_keys= ["科目名稱", "課程名稱", "subjectname", "coursename"]
    year_keys   = ["學年", "year"]
    sem_keys    = ["學期", "semester"]

    for df_idx, df in enumerate(df_list):
        cols = df.columns.tolist()

        # 建立 “无空白小写” 到 真实列名 的映射
        norm_map = {
            re.sub(r"\s+", "", col).lower(): col
            for col in cols
        }

        def find_col(keywords):
            for k in keywords:
                nk = re.sub(r"\s+", "", k).lower()
                if nk in norm_map:
                    return norm_map[nk]
            return None

        cred_col   = find_col(credit_keys)
        gpa_col    = find_col(gpa_keys)
        subj_col   = find_col(subject_keys)
        year_col   = find_col(year_keys)
        sem_col    = find_col(sem_keys)

        if not cred_col or not subj_col:
            # 这一张表格不包含学分或课程列，跳过
            continue

        buffer = ""  # 用于临时存放跨行的课程名称

        for _, row in df.iterrows():
            subj_raw = normalize_text(row.get(subj_col, ""))
            cred_txt = normalize_text(row.get(cred_col, ""))
            gpa_txt  = normalize_text(row.get(gpa_col, "")) if gpa_col else ""

            credit, parsed_gpa = parse_credit_and_gpa(cred_txt)
            _, parsed_gpa2 = parse_credit_and_gpa(gpa_txt)
            gpa = parsed_gpa2 or parsed_gpa

            # 判断这一行是否为“完整”记录
            is_complete = (
                credit > 0 or 
                is_passing_gpa(gpa) or
                subj_raw.upper() in {"通過", "抵免", "PASS", "EXEMPT"}
            )

            if not is_complete and subj_raw:
                # 不是完整记录，但有课程名称，累加到 buffer
                buffer = (buffer + " " + subj_raw).strip()
                continue

            if is_complete:
                # 拼接课程名称
                course_name = subj_raw
                if buffer:
                    course_name = (buffer + " " + subj_raw).strip()
                    buffer = ""

                # 学年学期（可能为空）
                year = normalize_text(row.get(year_col, "")) if year_col else ""
                sem  = normalize_text(row.get(sem_col, "")) if sem_col else ""

                record = {
                    "學年度": year,
                    "學期": sem,
                    "科目名稱": course_name,
                    "學分": credit,
                    "GPA": gpa,
                    "來源表格": df_idx + 1
                }

                if gpa and not is_passing_gpa(gpa):
                    failed_courses.append(record)
                else:
                    if credit > 0:
                        total_credits += credit
                    passed_courses.append(record)

        # 如果最后 buffer 里仍有未被处理的碎片，就扔掉
        buffer = ""

    return total_credits, passed_courses, failed_courses
