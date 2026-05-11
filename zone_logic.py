import streamlit as st

def handle_zone_selection(df, filtered_df):
    """
    Chức năng: Hiển thị bộ lọc khu vực và trả về dữ liệu đã lọc.
    """
    # Bạn hãy kiểm tra tên cột chính xác trong file JSON của mình (ví dụ: 'Khu vực' hoặc 'Zone')
    zone_col = 'Khu vực' 

    if zone_col in df.columns:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📍 Lọc theo Khu vực")
        
        # Lấy danh sách khu vực không trùng lặp
        list_zones = ["Tất cả"] + sorted(df[zone_col].unique().tolist())
        
        selected_zone = st.sidebar.selectbox(
            "Chọn khu tưới cần xem:", 
            list_zones,
            help="Chọn 'Tất cả' để xem tổng hợp toàn vườn"
        )
        
        # Thực hiện lọc nếu người dùng chọn một khu cụ thể
        if selected_zone != "Tất cả":
            filtered_df = filtered_df[filtered_df[zone_col] == selected_zone].copy()
            
        return filtered_df, selected_zone
    else:
        # Nếu không có cột Khu vực, trả về dữ liệu gốc và nhãn mặc định
        return filtered_df, "Toàn hệ thống"
