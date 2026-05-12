import streamlit as st

def handle_zone_selection(df, filtered_df):
    zone_col = "Tên khu" 

    if zone_col in df.columns:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📍 Lọc theo Khu vực")
        
        available_zones = df[zone_col].dropna().unique().tolist()
        list_zones = ["Tất cả"] + sorted([str(z).strip() for z in available_zones])
        
        selected_zone = st.sidebar.selectbox(
            "Chọn khu tưới cần xem:", 
            list_zones,
            help="Ưu tiên hiện lịch sử của khu đã chọn."
        )
        
        if selected_zone != "Tất cả":
            full_zone_df = df[df[zone_col].astype(str).str.strip() == selected_zone].copy()
            
            if len(full_zone_df) > 200: # Giới hạn xuống 500 điểm để cực mượt
                step = len(full_zone_df) // 200
                filtered_df = full_zone_df.iloc[::step].copy()
            else:
                filtered_df = full_zone_df
                
            st.sidebar.success(f"✨ Đã lọc xong khu: {selected_zone}")
        
        # 3. Xử lý thứ tự cột (Giữ nguyên)
        time_related_cols = [zone_col, 'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT']
        all_cols = filtered_df.columns.tolist()
        lead_cols = [c for c in time_related_cols if c in all_cols]
        remaining_cols = [c for c in all_cols if c not in lead_cols and c != 'Thời gian']
        column_order = lead_cols + ['Thời gian'] + remaining_cols
        
        return filtered_df, selected_zone, column_order
    else:
        return filtered_df, "Toàn hệ thống", filtered_df.columns.tolist()
