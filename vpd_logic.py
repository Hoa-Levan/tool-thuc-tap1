import streamlit as st
import pandas as pd
import numpy as np

def render_vpd_dashboard(df, filtered_df, view_mode, sel_label, current_zone):
    """
    Hàm xử lý độc lập giao diện và logic tính toán chỉ số VPD.
    Tách riêng hoàn toàn để tránh làm ảnh hưởng tới luồng xem số liệu tổng quan.
    """
    st.header("🌡️ Hệ thống Giám sát & Phân tích Áp suất Cây trồng (VPD)")
    
    # Kiểm tra xem file có đủ thông số tempKK và humiKK không
    if 'tempKK' not in df.columns or 'humiKK' not in df.columns:
        st.warning("⚠️ Tệp tin hiện tại không chứa thông số Nhiệt độ khí quyển (tempKK) hoặc Độ ẩm khí quyển (humiKK) cần thiết để tính toán chỉ số VPD.")
        return

    st.info("ℹ️ Chức năng phân tích toán học và cảnh báo ngưỡng sức khỏe cây trồng dựa trên VPD đang được thiết lập. Hãy quay lại sau!")
