import streamlit as st
from display_logic import get_chart_data

def show_charts(filtered_df, view_mode, display_type):
    st.subheader(f"📈 Biểu đồ diễn biến ({display_type})")
    
    # Giữ nguyên logic lọc chart_metrics của bạn
    numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
    chart_metrics = [m for m in numeric_cols if m not in ['Lưu lượng tổng', 'STT'] 
                     and filtered_df[m].notnull().any() and (filtered_df[m] != 0).any()]
    
    selected_m = st.multiselect("Thêm thông số:", chart_metrics, 
                                default=[chart_metrics[0]] if chart_metrics else [])

    if selected_m:
        chart_data = get_chart_data(filtered_df, view_mode, selected_m, display_type)
        # Vẽ biểu đồ
        st.line_chart(chart_data)
