import streamlit as st

def handle_zone_selection(df, filtered_df):
    zone_col = "Tên khu" 

    if zone_col in df.columns:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📍 Lọc theo Khu vực")
        
        # 1. Luôn hiện đầy đủ danh sách khu từ file gốc (df)
        available_zones = df[zone_col].dropna().unique().tolist()
        list_zones = ["Tất cả"] + sorted([str(z).strip() for z in available_zones])
        
        selected_zone = st.sidebar.selectbox(
            "Chọn khu tưới cần xem:", 
            list_zones,
            help="Nếu chọn một khu cụ thể, hệ thống sẽ ưu tiên hiện tất cả lịch sử của khu đó."
        )
        
        # 2. LOGIC ƯU TIÊN: 
        if selected_zone != "Tất cả":
            # ÉP hiện toàn bộ số liệu của khu này, bỏ qua filtered_df (thời gian) trước đó
            filtered_df = df[df[zone_col].astype(str).str.strip() == selected_zone].copy()
            st.sidebar.success(f"✨ Đang ưu tiên hiện toàn bộ dữ liệu của: {selected_zone}")
        
        # 3. Xử lý thứ tự cột hiển thị (giữ nguyên logic bạn đã có)
        time_related_cols = [zone_col, 'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT']
        all_cols = filtered_df.columns.tolist()
        lead_cols = [c for c in time_related_cols if c in all_cols]
        remaining_cols = [c for c in all_cols if c not in lead_cols and c != 'Thời gian']
        column_order = lead_cols + ['Thời gian'] + remaining_cols
        
        return filtered_df, selected_zone, column_order
    else:
        return filtered_df, "Toàn hệ thống", filtered_df.columns.tolist()
