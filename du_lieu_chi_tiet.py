import streamlit as st

def show_data_table(filtered_df):
    st.markdown("---")
    st.subheader("📋 Bảng dữ liệu chi tiết")
    # Giữ nguyên các lệnh hiển thị của bạn
    st.dataframe(filtered_df, use_container_width=True) 
    # Thêm nút tải CSV của bạn vào đây luôn
