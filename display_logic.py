import streamlit as st
import pandas as pd

def get_chart_data(filtered_df, view_mode, selected_m, display_type):
    """
    Logic để lấy dữ liệu biểu đồ:
    - display_type == "Số liệu trung bình": Dùng groupby (logic cũ)
    - display_type == "Số liệu mỗi lần đo": Dùng dữ liệu thô theo Thời gian
    """
    if not selected_m:
        return None

    if display_type == "Số liệu mỗi lần đo":
        # Lấy dữ liệu gốc, không gom nhóm, sắp xếp theo Thời gian
        chart_data = filtered_df.set_index('Thời gian')[selected_m].sort_index()
    else:
        # Logic "Số liệu trung bình cộng" (Giữ nguyên linh hồn code cũ của bạn)
        num_days = filtered_df['Ngày'].nunique()
        
        if num_days == 1 or view_mode == "Ngày" or view_mode == "Xem theo Giờ":
            chart_data = filtered_df.set_index('Thời gian')[selected_m].sort_index()
        else:
            # Gom nhóm trung bình theo ngày cho các chế độ xem dài hạn
            chart_data = filtered_df.groupby('Ngày')[selected_m].mean().sort_index()
            
    return chart_data.dropna(how='all')
