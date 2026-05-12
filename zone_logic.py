import streamlit as st

def handle_zone_selection(df, filtered_df):
    zone_col = "Tên khu" 

    if zone_col in df.columns:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📍 Lọc theo Khu vực")
        
        available_zones = df[zone_col].dropna().unique().tolist()
        list_zones = ["Tất cả"] + sorted([str(z) for z in available_zones])
        
        selected_zone = st.sidebar.selectbox("Chọn khu tưới cần xem:", list_zones)
        
        if selected_zone != "Tất cả":
            filtered_df = filtered_df[filtered_df[zone_col].astype(str).str.strip() == selected_zone.strip()].copy()
            
        # Tự động xử lý thứ tự cột để xuất ra bảng
        time_related_cols = [zone_col, 'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT']
        all_cols = filtered_df.columns.tolist()
        lead_cols = [c for c in time_related_cols if c in all_cols]
        remaining_cols = [c for c in all_cols if c not in lead_cols and c != 'Thời gian']
        
        column_order = lead_cols + ['Thời gian'] + remaining_cols
        
        # TRẢ VỀ ĐỦ 3 GIÁ TRỊ: dữ liệu, tên khu, và thứ tự cột
        return filtered_df, selected_zone, column_order
    else:
        # Nếu không có cột "Tên khu", trả về toàn bộ cột hiện có làm thứ tự mặc định
        return filtered_df, "Toàn hệ thống", filtered_df.columns.tolist()
