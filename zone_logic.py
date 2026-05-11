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
            filtered_df = filtered_df[filtered_df[zone_col].astype(str) == selected_zone].copy()
            
        # --- ĐOẠN CODE XỬ LÝ THỨ TỰ CỘT NHÉT VÀO ĐÂY ---
        time_related_cols = [zone_col, 'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT']
        all_cols = filtered_df.columns.tolist()
        lead_cols = [c for c in time_related_cols if c in all_cols]
        remaining_cols = [c for c in all_cols if c not in lead_cols and c != 'Thời gian']
        
        new_order = lead_cols + ['Thời gian'] + remaining_cols
        # Trả về thêm danh sách new_order
        return filtered_df, selected_zone, new_order
    else:
        all_cols = filtered_df.columns.tolist()
        return filtered_df, "Toàn hệ thống", all_cols
