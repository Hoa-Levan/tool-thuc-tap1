import streamlit as st
from display_logic import get_chart_data

def show_charts(filtered_df, view_mode, display_type):
    st.subheader(f"📈 Biểu đồ diễn biến ({display_type})")
    
    # --- BƯỚC 1: LỌC CỘT SỐ HỢP LỆ (Chỉ giữ lại 1 đoạn này) ---
    numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
    chart_metrics = [m for m in numeric_cols if m not in ['Lưu lượng tổng', 'STT'] 
                     and filtered_df[m].notnull().any() and (filtered_df[m] != 0).any()]
    
    # --- BƯỚC 2: CHỌN THÔNG SỐ ---
    selected_m = st.multiselect(
        "Thêm thông số vào biểu đồ:", 
        chart_metrics, 
        default=[chart_metrics[0]] if chart_metrics else []
    )

    if selected_m:
        # --- BƯỚC 3: LẤY DỮ LIỆU ĐÃ XỬ LÝ (Từ display_logic.py) ---
        chart_data = get_chart_data(filtered_df, view_mode, selected_m, display_type)
        
        # --- BƯỚC 4: HIỂN THỊ THÔNG BÁO HỖ TRỢ ---
        if view_mode == "Tuần" and filtered_df['Ngày'].nunique() == 1:
            single_date = filtered_df['Ngày'].iloc[0]
            st.info(f"💡 Dữ liệu tuần này chỉ có ngày **{single_date}**.")

        # --- BƯỚC 5: VẼ BIỂU ĐỒ ---
        if chart_data is not None:
            st.line_chart(chart_data)
