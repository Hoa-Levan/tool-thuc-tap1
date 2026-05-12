import streamlit as st
import pandas as pd

def handle_zone_selection(df, filtered_df):
    """
    Xử lý lọc theo khu vực với logic Ưu tiên:
    - Nếu chọn một khu cụ thể: Hiện tất cả dữ liệu của khu đó (vượt rào thời gian).
    - Nếu chọn 'Tất cả': Giữ nguyên dữ liệu đã lọc theo thời gian.
    """
    zone_col = "Tên khu" 

    if zone_col in df.columns:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📍 Lọc theo Khu vực")
        
        # 1. Lấy danh sách khu vực từ file gốc để luôn thấy đủ tên các khu
        # Dùng .strip() để tránh lỗi so sánh do khoảng trắng thừa
        available_zones = df[zone_col].dropna().unique().tolist()
        list_zones = ["Tất cả"] + sorted([str(z).strip() for z in available_zones])
        
        selected_zone = st.sidebar.selectbox(
            "Chọn khu tưới cần xem:", 
            list_zones,
            help="Nếu chọn khu cụ thể, hệ thống sẽ ưu tiên hiện tất cả lịch sử của khu đó."
        )
        
        # 2. LOGIC KHẮC PHỤC VẤN ĐỀ 2 (Ưu tiên hiển thị):
        if selected_zone != "Tất cả":
            # Khi chọn khu cụ thể, ta lọc lại từ 'df' gốc (không phải filtered_df)
            # Điều này giúp lấy được dữ liệu của khu đó ở bất kỳ ngày nào trong quá khứ
            full_zone_data = df[df[zone_col].astype(str).str.strip() == selected_zone].copy()
            
            if not full_zone_data.empty:
                # Ghi đè filtered_df bằng dữ liệu của riêng khu này
                filtered_df = full_zone_data
                
                # Thông báo cho người dùng biết khoảng thời gian thực tế của khu này
                min_d = filtered_df['Ngày'].min()
                max_d = filtered_df['Ngày'].max()
                st.sidebar.success(f"📅 Hiện dữ liệu {selected_zone}: \n{min_d} đến {max_d}")
            else:
                st.sidebar.warning(f"⚠️ Khu {selected_zone} không có dữ liệu.")
        
        # 3. Xử lý thứ tự cột để hiển thị bảng (giữ các cột quan trọng ở đầu)
        time_related_cols = [
            zone_col, 'Trạng thái', 'Phương thức hoạt động', 'Người điều khiển',
            'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT'
        ]
        
        all_cols = filtered_df.columns.tolist()
        # Lọc ra những cột thời gian/thông tin thực sự có trong dữ liệu
        lead_cols = [c for c in time_related_cols if c in all_cols]
        # Các cột còn lại (số liệu đo đạc)
        remaining_cols = [c for c in all_cols if c not in lead_cols and c != 'Thời gian']
        
        # Sắp xếp lại danh sách cột: Thông tin -> Thời gian -> Số liệu
        column_order = lead_cols + ['Thời gian'] + remaining_cols
        
        return filtered_df, selected_zone, column_order
    
    else:
        # Nếu file không có cột 'Tên khu'
        return filtered_df, "Toàn hệ thống", filtered_df.columns.tolist()
