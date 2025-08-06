import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="📄 成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    st.write("請上傳 PDF（純表格）格式的成績單檔案。")
    uploaded_file = st.file_uploader(
        "選擇一個成績單檔案（目前僅支援 PDF）",
        type="pdf"
    )

    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    with st.spinner("正在處理 PDF，請稍候..."):
        dfs = process_pdf_file(uploaded_file)

    if not dfs:
        st.warning(
            "未從 PDF 中提取到任何表格數據。"
            "請檢查 PDF 內容或嘗試調整 pdfplumber 的表格提取設定。"
        )
        return

    total_credits, passed, failed = calculate_total_credits(dfs)

    st.markdown("---")
    st.markdown("## ✅ 查詢結果")

    # 總學分：字體調大
    st.markdown(
        f"目前總學分：<span style='font-size:26px; font-weight:bold;'>{total_credits:.2f}</span>",
        unsafe_allow_html=True
    )

    target = st.number_input(
        "目標學分 (例如 128)",
        min_value=0.0,
        value=128.0,
        step=1.0
    )
    diff = target - total_credits

    # 還需學分：字體大小、字體顏色
    if diff > 0:
        st.markdown(
            f"還需 <span style='color:red; font-size:20px;'>{diff:.2f}</span> 學分",
            unsafe_allow_html=True
        )
    elif diff < 0:
        st.markdown(
            f"已超出畢業所需學分："
            f"<span style='color:red; font-size:20px;'>{abs(diff):.2f}</span>",
            unsafe_allow_html=True
        )
    else:
        st.markdown("剛好達到畢業所需學分。")

    st.markdown("---")
    st.markdown("### 📚 通過的課程列表")
    if passed:
        df_pass = pd.DataFrame(passed)[["學年度", "學期", "科目名稱", "學分", "GPA"]]
        st.dataframe(df_pass, height=300, use_container_width=True)
    else:
        st.info("沒有找到任何通過的課程。")

    if failed:
        st.markdown("---")
        st.markdown("### ⚠️ 不及格的課程列表")
        df_fail = pd.DataFrame(failed)[
            ["學年度", "學期", "科目名稱", "學分", "GPA", "來源表格"]
        ]
        st.dataframe(df_fail, height=200, use_container_width=True)
        st.info("這些科目因成績不及格而未計入總學分。")

    # CSV 下載按鈕
    if passed:
        csv_pass = pd.DataFrame(passed).to_csv(
            index=False, encoding="utf-8-sig"
        )
        st.download_button(
            "下載通過科目 CSV",
            data=csv_pass,
            file_name="passed_courses.csv",
            mime="text/csv"
        )
    if failed:
        csv_fail = pd.DataFrame(failed).to_csv(
            index=False, encoding="utf-8-sig"
        )
        st.download_button(
            "下載未通過科目 CSV",
            data=csv_fail,
            file_name="failed_courses.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
