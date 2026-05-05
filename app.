import streamlit as st
import pandas as pd
import json
from datetime import datetime

# Cấu hình giao diện
st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp", layout="wide")
st.title("📊 Công cụ Phân tích & Lọc dữ liệu Quan trắc")

# Chức năng nạp file
uploaded_file = st.file_uploader("Nạp tệp tin JSON của bạn", type=['json'])

def parse_time_series(value):
    """Hàm xử lý các chuỗi dữ liệu dạng 'thời gian/giá trị' trong file nhỏ giọt"""
    if not value or value == "0" or not isinstance(value, str):
        return None
    try:
        # Lấy giá trị cuối cùng trong chuỗi series (thường là giá trị mới nhất trước khi tắt)
        parts = value.strip().split(' ')
        last_val = parts[-1].split('/')[-1]
        return float(last_val)
    except:
        return None

if uploaded_file is not None:
    data = json.load(uploaded_file)
    df = pd.DataFrame(data)
    
    # 1. Chuẩn hóa dữ liệu
    df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S')
    df['Ngày'] = df['Thời gian'].dt.date
    
    # Xử lý chỉ số Áp suất (AS) - Có thể ở dạng số hoặc chuỗi series
    if 'AS' in df.columns:
        df['AS_Value'] = df['AS'].apply(lambda x: pd.to_numeric(x, errors='coerce') if '/' not in str(x) else parse_time_series(x))
    
    # Xử lý chỉ số Ánh sáng (soil_ASKK)
    if 'soil_ASKK' in df.columns:
        df['soil_ASKK'] = pd.to_numeric(df['soil_ASKK'], errors='coerce')

    # 2. Bộ lọc Ngày
    st.sidebar.header("Bộ lọc dữ liệu")
    list_days = sorted(df['Ngày'].unique(), reverse=True)
    selected_date = st.sidebar.selectbox("Chọn ngày cần xem:", list_days)

    if st.sidebar.button("Lọc và Phân tích"):
        filtered_df = df[df['Ngày'] == selected_date]
        
        st.subheader(f"📅 Kết quả lọc ngày: {selected_date}")
        
        # Hiển thị bảng dữ liệu gốc (đã lọc)
        with st.expander("Xem bảng dữ liệu chi tiết"):
            st.dataframe(filtered_df)

        # 3. Phân tích các chỉ số chính
        col1, col2, col3 = st.columns(3)

        # CỘT 1: ÁNH SÁNG (soil_ASKK)
        with col1:
            if 'soil_ASKK' in filtered_df.columns:
                avg_light = filtered_df['soil_ASKK'].mean()
                st.metric("Ánh sáng trung bình (Lux)", f"{avg_light:.2f}")
                # Ví dụ logic đánh giá ánh sáng
                if avg_light > 20000:
                    st.warning("☀️ Ánh sáng rất mạnh.")
                elif avg_light < 5000:
                    st.info("☁️ Ánh sáng yếu, có thể thiếu cho cây.")
                else:
                    st.success("✅ Ánh sáng đủ cho cây.")

        # CỘT 2: ÁP SUẤT (AS)
        with col2:
            if 'AS_Value' in filtered_df.columns:
                avg_pres = filtered_df['AS_Value'].mean()
                st.metric("Áp suất trung bình", f"{avg_pres:.2f}")
                if avg_pres > 1.5:
                    st.error("⚠️ Áp suất quá cao! Kiểm tra đường ống.")
                else:
                    st.success("✅ Áp suất ổn định.")

        # CỘT 3: LƯU LƯỢNG NƯỚC
        with col3:
            if 'Lưu lượng m2/h' in filtered_df.columns:
                flow_rate = pd.to_numeric(filtered_df['Lưu lượng m2/h'], errors='coerce').mean()
                st.metric("Lưu lượng tưới", f"{flow_rate:.2f} m²/h")
                st.caption("Chỉ số lượng nước trên 1m² trong 1 giờ.")

        # Biểu đồ diễn biến trong ngày
        st.subheader("📈 Biểu đồ diễn biến thời gian thực")
        chart_data = filtered_df.set_index('Thời gian')
        
        selected_metrics = st.multiselect(
            "Chọn chỉ số để vẽ biểu đồ:",
            [c for c in ['soil_ASKK', 'AS_Value', 'Lưu lượng m2/h', 'Nhiệt Độ', 'Độ ẩm'] if c in filtered_df.columns],
            default=['soil_ASKK'] if 'soil_ASKK' in filtered_df.columns else []
        )
        if selected_metrics:
            st.line_chart(chart_data[selected_metrics])
