import streamlit as st
import pandas as pd

def handle_hourly_view(df):
    """
    Xử lý logic chọn ngày và khoảng giờ.
    Trả về DataFrame đã lọc và nhãn hiển thị.
    """
    # 1. Chọn ngày trước (vì xem giờ phải gắn với một ngày cụ thể)
    all_days = sorted(df['Ngày'].unique(), reverse=True)
    sel_date = st.sidebar.selectbox("1. Chọn ngày:", all_days)
    
    # Lọc dữ liệu theo ngày đã chọn trước để lấy khoảng giờ có sẵn
    df_day = df[df['Ngày'] == sel_date].copy()
    
    # 2. Chọn khoảng giờ
    st.sidebar.markdown("---")
    st.sidebar.write("2. Chọn khoảng thời gian (Giờ):")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_hour = st.number_input("Từ (0-23h):", min_value=0, max_value=23, value=8)
    with col2:
        end_hour = st.number_input("Đến (0-23h):", min_value=0, max_value=23, value=17)

    if start_hour > end_hour:
        st.sidebar.error("Lỗi: Giờ bắt đầu phải nhỏ hơn giờ kết thúc!")
        return pd.DataFrame(), ""

    # 3. Tiến hành lọc theo giờ
    # Sử dụng thuộc tính .dt.hour của cột Thời gian
    filtered_df = df_day[
        (df_day['Thời gian'].dt.hour >= start_hour) & 
        (df_day['Thời gian'].dt.hour <= end_hour)
    ].copy()

    sel_label = f"Ngày {sel_date} (Từ {start_hour}h - {end_hour}h)"
    
    return filtered_df, sel_label
