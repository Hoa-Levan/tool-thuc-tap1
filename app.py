import streamlit as st
import pandas as pd
import json

# Cấu hình giao diện
st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp", layout="wide")
st.title("📊 Công cụ Phân tích & Lọc dữ liệu Đa năng")

# Chức năng nạp file
uploaded_file = st.file_uploader("Nạp tệp tin JSON của bạn", type=['json'])

def parse_time_series(value):
    """Hàm xử lý các chuỗi dữ liệu phức tạp dạng 'thời gian/giá trị'"""
    if not value or value == "0" or not isinstance(value, str):
        return None
    try:
        parts = value.strip().split(' ')
        last_val = parts[-1].split('/')[-1]
        return float(last_val)
    except:
        return None

if uploaded_file is not None:
    data = json.load(uploaded_file)
    df = pd.DataFrame(data)
    
    # 1. Chuẩn hóa dữ liệu & Ép kiểu số (Quan trọng để không bị trống biểu đồ)
    df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S')
    df['Ngày'] = df['Thời gian'].dt.date
    
    # Danh sách các cột cần chuyển sang số để vẽ biểu đồ
    cols_to_fix = ['soil_ASKK', 'Nhiệt Độ', 'Độ ẩm', 'Lưu lượng m2/h', 'tempKK', 'humiKK', 'EC', 'PH']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Xử lý riêng cho cột Áp suất AS
    if 'AS' in df.columns:
        df['AS_Value'] = df['AS'].apply(lambda x: pd.to_numeric(x, errors='coerce') if '/' not in str(x) else parse_time_series(x))

    # 2. Bộ lọc Ngày
    st.sidebar.header("Bộ lọc dữ liệu")
    list_days = sorted(df['Ngày'].unique(), reverse=True)
    selected_date = st.sidebar.selectbox("Chọn ngày cần xem:", list_days)

    if selected_date:
        filtered_df = df[df['Ngày'] == selected_date].sort_values('Thời gian')
        
        st.subheader(f"📅 Phân tích chi tiết ngày: {selected_date}")
        
        # 3. Khu vực Đánh giá thông số (Đa chỉ số)
        st.markdown("### 📝 Đánh giá chuyên sâu")
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if 'soil_ASKK' in filtered_df.columns:
                val = filtered_df['soil_ASKK'].mean()
                st.metric("Ánh sáng (Lux)", f"{val:.1f}")
                if val > 15000: st.warning("☀️ Ánh sáng rất mạnh")
                elif val < 5000: st.info("☁️ Ánh sáng yếu")
                else: st.success("✅ Ánh sáng tối ưu")

        with c2:
            # Ưu tiên lấy nhiệt độ không khí (tempKK) hoặc nhiệt độ đất
            t_col = 'tempKK' if 'tempKK' in filtered_df.columns else 'Nhiệt Độ'
            if t_col in filtered_df.columns:
                val = filtered_df[t_col].mean()
                # Kiểm tra nếu nhiệt độ bị nhân 10 (ví dụ 331 thay vì 33.1)
                if val > 100: val = val / 10 
                st.metric("Nhiệt độ (°C)", f"{val:.1f}")
                if val > 35: st.error("🔥 Quá nóng!")
                elif val < 18: st.info("❄️ Trời lạnh")
                else: st.success("✅ Nhiệt độ ổn định")

        with c3:
            h_col = 'humiKK' if 'humiKK' in filtered_df.columns else 'Độ ẩm'
            if h_col in filtered_df.columns:
                val = filtered_df[h_col].mean()
                st.metric("Độ ẩm (%)", f"{val:.1f}%")
                if val < 40: st.warning("🌵 Độ ẩm thấp (khô)")
                else: st.success("✅ Độ ẩm tốt")

        with c4:
            if 'AS_Value' in filtered_df.columns:
                val = filtered_df['AS_Value'].mean()
                st.metric("Áp suất (AS)", f"{val:.2f}")
                if val > 0: st.success("💧 Hệ thống đang vận hành")
                else: st.info("💤 Hệ thống đang nghỉ")

        # 4. Biểu đồ động (Chọn gì hiện nấy)
        st.subheader("📈 Biểu đồ diễn biến theo thời gian")
        
        # Tự động tìm các cột có dữ liệu số
        numeric_cols = [c for c in ['soil_ASKK', 'AS_Value', 'Lưu lượng m2/h', 'tempKK', 'humiKK', 'Nhiệt Độ', 'Độ ẩm', 'EC', 'PH'] if c in filtered_df.columns]
        
        selected_metrics = st.multiselect(
            "Bấm vào đây để chọn/thêm thông số muốn xem biểu đồ:",
            options=numeric_cols,
            default=[numeric_cols[0]] if numeric_cols else []
        )
        
        if selected_metrics:
            # Vẽ biểu đồ với trục X là thời gian
            chart_df = filtered_df.set_index('Thời gian')[selected_metrics]
            st.line_chart(chart_df)
        else:
            st.warning("Vui lòng chọn ít nhất một thông số để hiển thị biểu đồ.")

        with st.expander("Xem bảng dữ liệu gốc"):
            st.write(filtered_df)
