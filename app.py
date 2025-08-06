import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.title("📄 成績單學分計算工具")
    uploaded_file = st.file_uploader("選擇一個 PDF 或 DOCX 檔案", type=["pdf","docx"])
    if not uploaded_file:
        return

    filename = uploaded_file.name.lower()
    if filename.endswith(".pdf"):
        dfs = process_pdf_file(uploaded_file)
    else:  # .docx
        dfs = process_docx_file(uploaded_file)

    if not dfs:
        st.warning("未能擷取到任何表格，請確認檔案格式或內容。")
        return

    total, passed, failed = calculate_total_credits(dfs)
    st.success(f"目前總學分：{total:.2f}")

    if passed:
        st.dataframe(pd.DataFrame(passed)[["學年度","學期","科目名稱","學分","GPA"]])
    if failed:
        st.markdown("#### ⚠️ 不及格科目")
        st.dataframe(pd.DataFrame(failed)[["學年度","學期","科目名稱","學分","GPA"]])
