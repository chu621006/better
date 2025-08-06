# app.py
import os
import streamlit as st
from utils.grade_analysis import calculate_total_credits
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file  # 你需要自己实现这个模块

def main():
    st.set_page_config(page_title="📄 成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # 上傳區改為同時支持 PDF 和 DOCX
    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    uploaded_file = st.file_uploader(
        "選擇一個成績單檔案（支援 PDF, DOCX）",
        type=["pdf", "docx"]
    )
    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    # 根據副檔名分流
    filename = uploaded_file.name.lower()
    if filename.endswith(".pdf"):
        dfs = process_pdf_file(uploaded_file)
    elif filename.endswith(".docx"):
        dfs = process_docx_file(uploaded_file)
    else:
        st.error("不支援的檔案格式。")
        return

    # 計算總學分
    total_credits, passed, failed = calculate_total_credits(dfs)

    st.markdown("---")
    # 調整文字大小：總學分比「查詢結果」小一號
    st.markdown(
        "<div style='font-size:20px;'>目前總學分: "
        f"<span style='font-size:24px; color:green;'>{total_credits:.2f}</span></div>",
        unsafe_allow_html=True
    )

    # 還需學分，數字用紅色
    target = st.number_input(
        "目標學分 (例如 128)", min_value=0.0, value=128.0, step=1.0
    )
    diff = target - total_credits
    if diff > 0:
        st.markdown(
            "<div style='font-size:20px;'>還需 "
            f"<span style='color:red;'>{diff:.2f}</span> 學分</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='font-size:20px;'>已超出 "
            f"<span style='color:red;'>{abs(diff):.2f}</span> 學分</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    # 通過的課程列表
    st.markdown("### 📚 通過的課程列表")
    if passed:
        df_passed = st.dataframe(
            passed, use_container_width=True
        )
        csv_passed = st.experimental_get_query_params()  # 這裡可依需求調整
    else:
        st.info("沒有找到任何通過的課程。")

    # 不及格的課程列表
    if failed:
        st.markdown("### ⚠️ 不及格的課程列表")
        st.dataframe(failed, use_container_width=True)
    # CSV 下載按鈕（按需保留）
    if passed:
        csv_data = "\n".join([",".join(map(str, row.values())) for row in passed])
        st.download_button("下載通過課程 CSV", data=csv_data, file_name="passed.csv")
    if failed:
        csv_data = "\n".join([",".join(map(str, row.values())) for row in failed])
        st.download_button("下載不及格課程 CSV", data=csv_data, file_name="failed.csv")

if __name__ == "__main__":
    main()
