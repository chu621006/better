# app.py
import streamlit as st
import pandas as pd

from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="PDF/DOCX 成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    uploaded_file = st.file_uploader("選擇檔案", type=["pdf", "docx"])

    if not uploaded_file:
        st.info("請上傳檔案開始處理。")
        return

    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        dfs = process_pdf_file(uploaded_file)
    else:
        dfs = process_docx_file(uploaded_file)

    if not dfs:
        st.warning("❌ 未從檔案中提取到任何表格。請確認檔案內容或格式是否正確。")
        return

    total_credits, passed_courses, failed_courses = calculate_total_credits(dfs)

    st.markdown("---")
    st.success(f"目前總學分：**{total_credits:.2f}**")

    # 目標學分輸入
    target = st.number_input("目標學分 (例如 128)", min_value=0.0, value=128.0, step=1.0)
    diff = target - total_credits
    if diff > 0:
        st.info(f"距離畢業學分還差：**{diff:.2f}**")
    else:
        st.info(f"已超過畢業學分 **{abs(diff):.2f}**")

    st.markdown("### 📚 通過課程")
    if passed_courses:
        df_pass = pd.DataFrame(passed_courses)
        st.dataframe(df_pass[["學年度","學期","科目名稱","學分","GPA"]])
    else:
        st.info("沒有找到任何通過的課程。")

    if failed_courses:
        st.markdown("### ⚠️ 不及格課程")
        df_fail = pd.DataFrame(failed_courses)
        st.dataframe(df_fail[["學年度","學期","科目名稱","學分","GPA"]])

if __name__ == "__main__":
    main()
