import streamlit as st

def handle_zone_selection(df, filtered_df):
    """
    Chức năng: Hiển thị bộ lọc và thực hiện lọc dữ liệu theo cột 'Tên khu'.
    """
    # Gán tên cột chính xác như trong file JSON của bạn
    zone_col = "Tên khu" 

    if zone_col in df.columns:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📍 Lọc theo Khu vực")
        
        # Lấy danh sách các khu vực duy nhất, loại bỏ giá trị trống
        available_zones = df[zone_col].dropna().unique().tolist()
        # Chuyển tất cả sang chuỗi và sắp xếp để hiển thị chuyên nghiệp
        list_zones = ["Tất cả"] + sorted([str(z) for z in available_zones])
        
        selected_zone = st.sidebar.selectbox(
            "Chọn khu tưới cần xem:", 
            list_zones,
            key="zone_selector" # Thêm key để tránh trùng lặp widget
        )
        
        # Thực hiện lọc dữ liệu
        if selected_zone != "Tất cả":
            # Ép kiểu về string khi so sánh để đảm bảo khớp 100%
            filtered_df = filtered_df[filtered_df[zone_col].astype(str) == selected_zone].copy()
            
        return filtered_df, selected_zone
    else:
        # Nếu file JSON không có cột 'Tên khu', báo lỗi nhẹ để người dùng biết
        st.sidebar.warning(f"⚠️ Không tìm thấy cột '{zone_col}'")
        return filtered_df, "Toàn hệ thống"
