import pandas as pd

def get_chart_data(filtered_df, view_mode, selected_m, display_type):
    """
    Hàm này lấy dữ liệu biểu đồ dựa trên lựa chọn của người dùng.
    """
    # KIỂM TRA SỐ LƯỢNG NGÀY THỰC TẾ
    num_days = filtered_df['Ngày'].nunique()

    # TRƯỜNG HỢP 1: Người dùng muốn xem dữ liệu gốc (Mỗi lần đo)
    if display_type == "Số liệu mỗi lần đo":
        return filtered_df.set_index('Thời gian')[selected_m].sort_index().dropna(how='all')

    # TRƯỜNG HỢP 2: Người dùng muốn xem "Số liệu trung bình cộng" (Logic cũ của bạn)
    if num_days == 1:
        # Trường hợp chỉ có 1 ngày: ép vẽ theo Thời gian chi tiết để hiện đường kẻ
        return filtered_df.set_index('Thời gian')[selected_m].sort_index().dropna(how='all')
    else:
        # Trường hợp có nhiều ngày:
        if view_mode == "Ngày" or view_mode == "Xem theo Giờ":
            return filtered_df.set_index('Thời gian')[selected_m].sort_index().dropna(how='all')
        else:
            # Gom nhóm trung bình cho Tuần, Tháng, Năm...
            return filtered_df.groupby('Ngày')[selected_m].mean().dropna(how='all')
