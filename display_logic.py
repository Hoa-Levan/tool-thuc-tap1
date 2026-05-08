import pandas as pd

def get_chart_data(filtered_df, view_mode, selected_m, display_type):
    # Nếu muốn xem chi tiết từng lần đo
    if display_type == "Số liệu mỗi lần đo":
        return filtered_df.set_index('Thời gian')[selected_m].sort_index().dropna(how='all')

    # Nếu muốn xem trung bình cộng (Logic cũ của bạn)
    num_days = filtered_df['Ngày'].nunique()
    
    # Chỉ có 1 ngày hoặc đang ở chế độ xem theo giờ/ngày -> Hiện chi tiết Thời gian
    if num_days == 1 or view_mode == "Ngày" or view_mode == "Xem theo Giờ":
        return filtered_df.set_index('Thời gian')[selected_m].sort_index().dropna(how='all')
    else:
        # Xem theo Tuần/Tháng/Năm -> Gom nhóm trung bình theo Ngày
        return filtered_df.groupby('Ngày')[selected_m].mean().dropna(how='all')
