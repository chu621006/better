import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="PDF/Word 成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    st.write("請上傳 PDF（純表格）格式的成績單檔案，工具將嘗試提取其中的表格數據並計算總學分。")
    st.write("您也可以輸入目標學分，查看還差多少學分。")

    uploaded_file = st.file_uploader(
        "選擇一個成績單檔案（目前僅支援 PDF）",
        type=["pdf"]
    )

    if uploaded_file is not None:
        st.success(f"已上傳檔案: **{uploaded_file.name}**")
        with st.spinner("正在處理檔案，請稍候..."):
            dfs = process_pdf_file(uploaded_file)

        if dfs:
            total_credits, calculated_courses, failed_courses = calculate_total_credits(dfs)

            st.markdown("---")
            # 查詢結果區塊
            st.markdown("## ✅ 查詢結果")
            # 總學分（加大一點）
            st.markdown(
                f"<span style='font-size:32px; font-weight:bold;'>目前總學分: {total_credits:.2f}</span>",
                unsafe_allow_html=True
            )

            # 目標學分輸入
            target = st.number_input(
                "目標學分 (例如：128)",
                min_value=0.0,
                value=128.0,
                step=1.0
            )
            diff = target - total_credits
            # 「還需」文字及數字
            color = "red" if diff > 0 else "green"
            st.markdown(
                f"<span style='font-size:24px;'>還需 </span>"
                f"<span style='font-size:24px; color:{color};'>{diff:.2f}</span>"
                f"<span style='font-size:24px;'> 學分</span>",
                unsafe_allow_html=True
            )

            st.markdown("---")
            # 通過的課程列表（改成動態欄位檢查）
            st.markdown("### 📚 通過的課程列表")
            if calculated_courses:
                df_pass = pd.DataFrame(calculated_courses)
                desired = ["學年度", "學期", "科目名稱", "學分", "GPA"]
                cols = [c for c in desired if c in df_pass.columns]
                if cols:
                    st.dataframe(df_pass[cols], height=300, use_container_width=True)
                else:
                    st.warning("⚠️ 通過課程的表格欄位不符合預期，無法顯示。")
            else:
                st.info("沒有找到任何通過的課程。")

            # 不及格的課程列表（同理做動態欄位檢查）
            if failed_courses:
                st.markdown("---")
                st.markdown("### ⚠️ 不及格的課程列表")
                df_fail = pd.DataFrame(failed_courses)
                want_fail = ["學年度", "學期", "科目名稱", "學分", "GPA", "來源表格"]
                cols_fail = [c for c in want_fail if c in df_fail.columns]
                if cols_fail:
                    st.dataframe(df_fail[cols_fail], height=200, use_container_width=True)
                else:
                    st.warning("⚠️ 不及格課程的表格欄位不符合預期，無法顯示。")
                st.info("這些科目因成績不及格 ('D','E','F' 等) 而未計入總學分。")

            # 下載按鈕
            if calculated_courses:
                csv_pass = pd.DataFrame(calculated_courses).to_csv(
                    index=False, encoding="utf-8-sig"
                )
                st.download_button(
                    "下載通過科目列表 (CSV)",
                    data=csv_pass,
                    file_name=f"{uploaded_file.name}_passed.csv",
                    mime="text/csv"
                )
            if failed_courses:
                csv_fail = pd.DataFrame(failed_courses).to_csv(
                    index=False, encoding="utf-8-sig"
                )
                st.download_button(
                    "下載不及格科目列表 (CSV)",
                    data=csv_fail,
                    file_name=f"{uploaded_file.name}_failed.csv",
                    mime="text/csv"
                )

        else:
            st.warning("⚠️ 未從檔案中找到任何表格，請檢查檔案內容或格式是否正確。")
    else:
        st.info("請先上傳檔案，以開始學分計算。")

if __name__ == "__main__":
    main()
