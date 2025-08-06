# utils/grade_analysis.py

import re

def normalize_text(cell):
    """
    将任意内容转为字符串，去除多余空白（包括换行）。
    """
    if cell is None:
        return ""
    text = str(cell)
    return re.sub(r'\s+', ' ', text).strip()

def is_passing_gpa(gpa_str):
    """
    判断一个 GPA 字符串是否为“及格”。
    支持 A~F+/-、数字分数(>=60)、以及“通過”“抵免”等。
    """
    gpa = normalize_text(gpa_str).upper()
    if not gpa:
        return False

    if gpa in {"通過", "抵免", "PASS", "EXEMPT"}:
        return True
    if gpa in {"D", "D-", "E", "F", "X", "不通過", "未通過", "不及格"}:
        return False
    if re.fullmatch(r"[A-C][+-]?", gpa):
        return True
    if gpa.replace('.', '', 1).isdigit():
        try:
            return float(gpa) >= 60.0
        except:
            pass
    return False

def parse_credit_and_gpa(txt):
    """
    从一段文本中解析出 (credit: float, gpa: str)。
    支持：
      - "A 2" 或 "A- 3"
      - "2 A" 或 "3.0 B+"
      - 纯数字(学分)
      - 纯字母成绩(只返回 GPA)
      - 通過/抵免
    """
    s = normalize_text(txt)
    # 通过/抵免
    if s.upper() in {"通過", "抵免", "PASS", "EXEMPT"}:
        return 0.0, s

    # A 2
    m = re.match(r"^([A-Fa-f][+-]?)[\s,／/]*(\d+(\.\d+)?)$", s)
    if m:
        return float(m.group(2)), m.group(1).upper()
    # 2 A
    m = re.match(r"^(\d+(\.\d+)?)[\s,／/]*([A-Fa-f][+-]?)$", s)
    if m:
        return float(m.group(1)), m.group(3).upper()
    # 纯学分
    m = re.fullmatch(r"\d+(\.\d+)?", s)
    if m:
        return float(s), ""
    # 纯 GPA
    m = re.fullmatch(r"[A-Fa-f][+-]?|通過|抵免|PASS|EXEMPT", s, re.IGNORECASE)
    if m:
        return 0.0, m.group(0).upper()
    return 0.0, ""

def calculate_total_credits(df_list):
    """
    传入一个由 pandas.DataFrame 组成的列表（每个都是成绩表格），
    自动识别“学分”“科目名称”“GPA”“学年”“学期”列，
    并且对跨行的课程名称进行缓冲合并，最后返回：
      total_credits: float
      passed_courses: list of dict
      failed_courses: list of dict
    """
    total_credits = 0.0
    passed_courses = []
    failed_courses = []

    # 不同格式下可能的列关键字
    credit_keys   = ["學分", "credits", "credit"]
    gpa_keys      = ["GPA", "成績", "grade"]
    subject_keys  = ["科目名稱", "課程名稱", "subjectname", "coursename"]
    year_keys     = ["學年", "year"]
    semester_keys = ["學期", "semester"]

    for df_idx, df in enumerate(df_list):
        cols = df.columns.tolist()
        # 规范化列名映射
        norm_map = {
            re.sub(r"\s+", "", c).lower(): c
            for c in cols
        }
        def find_col(keywords):
            for k in keywords:
                nk = re.sub(r"\s+", "", k).lower()
                if nk in norm_map:
                    return norm_map[nk]
            return None

        cred_col  = find_col(credit_keys)
        gpa_col   = find_col(gpa_keys)
        subj_col  = find_col(subject_keys)
        year_col  = find_col(year_keys)
        sem_col   = find_col(semester_keys)

        # 如果没有学分列或课程列，就跳过
        if not cred_col or not subj_col:
            continue

        buffer = ""  # 用于跨行课程名累积

        # 遍历每行
        for _, row in df.iterrows():
            subj_txt = normalize_text(row.get(subj_col, ""))
            cred_txt = normalize_text(row.get(cred_col, ""))
            gpa_txt  = normalize_text(row.get(gpa_col, "")) if gpa_col else ""

            credit, gpa1 = parse_credit_and_gpa(cred_txt)
            _,      gpa2 = parse_credit_and_gpa(gpa_txt)
            gpa = gpa2 or gpa1

            # 判定是否构成一条完整记录
            is_complete = (
                credit > 0 or
                is_passing_gpa(gpa) or
                subj_txt.upper() in {"通過", "抵免", "PASS", "EXEMPT"}
            )

            if not is_complete and subj_txt:
                # 只有课程名，累积到 buffer
                buffer = (buffer + " " + subj_txt).strip()
                continue

            if is_complete:
                # 拼接最终课程名
                course_name = (buffer + " " + subj_txt).strip() if buffer else subj_txt
                buffer = ""

                year = normalize_text(row.get(year_col, "")) if year_col else ""
                sem  = normalize_text(row.get(sem_col, "")) if sem_col else ""

                rec = {
                    "學年度": year,
                    "學期": sem,
                    "科目名稱": course_name,
                    "學分": credit,
                    "GPA": gpa,
                    "來源表格": df_idx + 1
                }

                if gpa and not is_passing_gpa(gpa):
                    failed_courses.append(rec)
                else:
                    if credit > 0:
                        total_credits += credit
                    passed_courses.append(rec)

        # 最后扔掉残留 buffer
        buffer = ""

    return total_credits, passed_courses, failed_courses
