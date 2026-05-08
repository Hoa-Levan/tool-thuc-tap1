import pandas as pd

def get_chart_data(filtered_df, view_mode, selected_m, display_type):
    # Đảm bảo cột Thời gian là định dạng datetime để resample không lỗi
    filtered_df['Thời gian'] = pd.to_datetime(filtered_df['Thời gian'])
    
    # TRƯỜNG HỢP 1: XEM MỖI LẦN ĐO (Dữ liệu thô - Nhìn thấy mọi răng cưa)
    if display_type == "Số liệu mỗi lần đo":
        return filtered_df.set_index('Thời gian')[selected_m].sort_index().dropna(how='all')

    # TRƯỜNG HỢP 2: XEM TRUNG BÌNH CỘNG (Làm mượt dữ liệu)
    num_days = filtered_df['Ngày'].nunique()

    # Nếu xem theo Ngày: Làm mượt bằng cách lấy trung bình mỗi 1 giờ (1H)
    if view_mode == "Ngày" or (view_mode == "Tuần" and num_days == 1):
        temp_df = filtered_df.set_index('Thời gian')[selected_m].sort_index()
        return temp_df.resample('1H').mean().dropna(how='all')

    # Nếu xem theo Giờ: Làm mượt bằng cách lấy trung bình mỗi 5 phút (5min)
    elif view_mode == "Xem theo Giờ":
        temp_df = filtered_df.set_index('Thời gian')[selected_m].sort_index()
        return temp_df.resample('5min').mean().dropna(how='all')

    # Nếu xem theo Tuần, Tháng, Năm (nhiều ngày): Gom nhóm trung bình theo Ngày (Logic cũ)
    else:
        return filtered_df.groupby('Ngày')[selected_m].mean().sort_index().dropna(how='all')
