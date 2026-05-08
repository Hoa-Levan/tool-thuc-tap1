import pandas as pd
import streamlit as st

def get_chart_data(filtered_df, view_mode, selected_m, display_type):
    # Bước 1: Chuẩn hóa thời gian và index
    df_plot = filtered_df.copy()
    df_plot['Thời gian'] = pd.to_datetime(df_plot['Thời gian'])
    df_plot = df_plot.set_index('Thời gian').sort_index()

    # TRƯỜNG HỢP 1: XEM MỖI LẦN ĐO (Dữ liệu gốc - Điền 0 vào ô rỗng)
    if display_type == "Số liệu mỗi lần đo":
        # .fillna(0) sẽ biến tất cả các ô None/NaN trong file gốc thành số 0 trên biểu đồ
        return df_plot[selected_m].fillna(0)

    # TRƯỜNG HỢP 2: XEM TRUNG BÌNH CỘNG
    num_days = filtered_df['Ngày'].nunique()
    try:
        # Nếu xem theo Ngày: Gom trung bình mỗi 1 tiếng, nếu tiếng đó không có dữ liệu thì hiện 0
        if view_mode == "Ngày" or num_days == 1:
            return df_plot[selected_m].resample('h').mean().fillna(0)

        # Nếu xem theo Giờ: Gom trung bình mỗi 5 phút, nếu không có dữ liệu thì hiện 0
        elif view_mode == "Xem theo Giờ":
            return df_plot[selected_m].resample('5min').mean().fillna(0)

        # Nếu xem theo Tuần, Tháng, Năm (nhiều ngày): Gom theo Ngày
        else:
            return filtered_df.groupby('Ngày')[selected_m].mean().sort_index().fillna(0)
            
    except Exception as e:
        # Nếu có lỗi bất ngờ, cứ hiện dữ liệu gốc và điền 0 vào chỗ rỗng
        return df_plot[selected_m].fillna(0)
