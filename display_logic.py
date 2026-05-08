import pandas as pd
import streamlit as st

def get_chart_data(filtered_df, view_mode, selected_m, display_type):
    # Bước 1: Ép kiểu dữ liệu thời gian chuẩn xác
    df_plot = filtered_df.copy()
    df_plot['Thời gian'] = pd.to_datetime(df_plot['Thời gian'])
    df_plot = df_plot.set_index('Thời gian').sort_index()

    # TRƯỜNG HỢP 1: XEM MỖI LẦN ĐO (Dữ liệu gốc, sát file nhất)
    if display_type == "Số liệu mỗi lần đo":
        # Không resample, không làm mượt. Giữ nguyên từng điểm đo.
        return df_plot[selected_m]

    # TRƯỜNG HỢP 2: XEM TRUNG BÌNH CỘNG (Làm mượt để thấy xu hướng)
    num_days = filtered_df['Ngày'].nunique()

    try:
        # Nếu xem theo Ngày hoặc chỉ có 1 ngày dữ liệu: Gom trung bình mỗi 30 phút (30min)
        if view_mode == "Ngày" or num_days == 1:
            return df_plot[selected_m].resample('30min').mean().dropna(how='all')

        # Nếu xem theo Giờ: Gom trung bình mỗi 5 phút (5min)
        elif view_mode == "Xem theo Giờ":
            return df_plot[selected_m].resample('5min').mean().dropna(how='all')

        # Nếu xem theo Tuần, Tháng, Năm: Gom theo Ngày (Logic cũ của bạn)
        else:
            # Quay lại dùng cột Ngày để group cho chính xác với lịch
            return filtered_df.groupby('Ngày')[selected_m].mean().sort_index().dropna(how='all')
    except Exception as e:
        st.error(f"Lỗi xử lý làm mượt dữ liệu: {e}")
        return df_plot[selected_m]
