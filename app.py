import streamlit as st
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")
    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")

    uploaded_file = st.file_uploader("選擇一個檔案", type=["pdf", "docx"])
    if not uploaded_file:
        st.info("請先上傳檔案以開始處理。")
        return

    filename = uploaded_file.name.lower()
    if filename.endswith(".pdf"):
        dfs = process_pdf_file(uploaded_file)
    elif filename.endswith(".docx"):
        dfs = process_docx_file(uploaded_file)
    else:
        st.error("只支援 PDF（純表格）或 Word (.docx)！")
        return

    if not dfs:
        st.warning("未從檔案中提取到任何表格資料。")
        return

    total_credits, passed_courses, failed_courses = calculate_total_credits(dfs)

    st.markdown("---")
    st.markdown("## ✅ 查詢結果")
    st.markdown(f"目前總學分: **{total_credits:.2f}**")

    target = st.number_input("目標學分 (例如 128)", min_value=0.0, value=128.0, step=1.0)
    diff = target - total_credits
    if diff > 0:
        st.write(f"還需 **{diff:.2f}** 學分")
    else:
        st.write(f"已超出 **{abs(diff):.2f}** 學分")

    st.markdown("---")
    st.markdown("### 📚 通過的課程列表")
    if passed_courses:
        df_pass = st.dataframe(
            {k: [c[k] for c in passed_courses] for k in passed_courses[0]},
            use_container_width=True
        )
    else:
        st.info("沒有找到任何通過的課程。")

    if failed_courses:
        st.markdown("### ⚠️ 不及格的課程列表")
        st.dataframe(
            {k: [c[k] for c in failed_courses] for k in failed_courses[0]},
            use_container_width=True
        )

if __name__ == "__main__":
    main()
