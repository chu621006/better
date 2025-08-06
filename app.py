# app.py

import streamlit as st
import pandas as pd

from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file  # 如果沒有處理 .docx 的功能，可以註解掉
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="📄 成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")
    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")

    uploaded_file = st.file_uploader("選擇一個檔案", type=["pdf", "docx"])
    if uploaded_file is None:
        st.info("請先上傳檔案。")
        return

    filename = uploaded_file.name.lower()
    # 1️⃣ 依副檔名呼叫不同的處理函式
    if filename.endswith(".pdf"):
        dfs = process_pdf_file(uploaded_file)
    elif filename.endswith(".docx"):
        dfs = process_docx_file(uploaded_file)
    else:
        st.error("不支援的檔案格式。請上傳 .pdf 或 .docx。")
        return

    if not dfs:
        st.warning("未從檔案中提取到任何表格。請確認檔案內容或格式是否正確。")
        return

    # 2️⃣ 計算學分
    total_credits, calculated_courses, failed_courses = calculate_total_credits(dfs)

    # 3️⃣ 讓使用者輸入目標學分
    st.markdown("---")
    target_credits = st.number_input(
        "目標學分 (例如：128)", 
        min_value=0.0, 
        value=128.0, 
        step=1.0
    )
    credit_difference = target_credits - total_credits

    # ── 4️⃣ 自訂「查詢結果」區塊排版與樣式 ──
    st.markdown(
        f"""
        ## ✅ 查詢結果

        <p style="margin-top:-0.5em; margin-bottom:0.2em;">
          目前總學分：
          <span style="font-size:1.8rem; color:green; font-weight:bold;">
            {total_credits:.2f}
          </span>
        </p>
        """,
        unsafe_allow_html=True
    )

    if credit_difference > 0:
        st.markdown(
            f"""
            <p style="font-size:1.8rem; margin-top:-0.2em;">
              還需 
              <span style="color:red; font-weight:bold;">{credit_difference:.2f}</span>
              學分
            </p>
            """,
            unsafe_allow_html=True
        )
    elif credit_difference < 0:
        st.markdown(
            f"""
            <p style="font-size:1.8rem; margin-top:-0.2em;">
              已超出畢業學分 
              <span style="color:red; font-weight:bold;">{abs(credit_difference):.2f}</span>
            </p>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<p style='font-size:1.8rem; margin-top:-0.2em;'>恭喜！已達到畢業所需學分 🎉</p>",
            unsafe_allow_html=True
        )

    # 5️⃣ 顯示「通過的課程列表」
    st.markdown("---")
    st.markdown("### 📚 通過的課程列表")
    if calculated_courses:
        df_pass = pd.DataFrame(calculated_courses)
        st.dataframe(df_pass[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)
    else:
        st.info("沒有找到任何通過的課程。")

    # 6️⃣ 顯示「不及格的課程列表」
    if failed_courses:
        st.markdown("---")
        st.markdown("### ⚠️ 不及格的課程列表")
        df_fail = pd.DataFrame(failed_courses)
        st.dataframe(df_fail[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)

    # 7️⃣ CSV 下載按鈕
    if calculated_courses:
        csv_pass = pd.DataFrame(calculated_courses).to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載通過課程列表 (CSV)", csv_pass, file_name="passed_courses.csv", mime="text/csv")
    if failed_courses:
        csv_fail = pd.DataFrame(failed_courses).to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載不及格課程列表 (CSV)", csv_fail, file_name="failed_courses.csv", mime="text/csv")

if __name__ == "__main__":
    main()
