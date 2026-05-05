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
    
    # 1. Chuẩn hóa dữ liệu & Ép kiểu số
    df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
    df = df.dropna(subset=['Thời gian']) # Bỏ dòng lỗi thời gian
    df['Ngày'] = df['Thời gian'].dt.date
    
    # Danh sách tất cả các cột tiềm năng từ cả 2 loại file
    cols_to_fix = ['soil_ASKK', 'Nhiệt Độ', 'Độ ẩm', 'Lưu lượng m2/h', 'Lưu lượng tổng', 'tempKK', 'humiKK', 'EC', 'PH', 'TBEC', 'TBPH']
    
    for col in cols_to_fix:
        if col in df.columns:
            # Ép kiểu số an toàn, tránh lỗi TypeError khi so sánh
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Xử lý riêng cho cột Áp suất AS (để xử lý chuỗi 16-01-59/1.05)
    if 'AS' in df.columns:
        df['AS_Value'] = df['AS'].apply(lambda x: pd.to_numeric(x, errors='coerce') if '/' not in str(x) else parse_time_series(x))

    # 2. Bộ lọc Ngày
    st.sidebar.header("Bộ lọc dữ liệu")
    list_days = sorted(df['Ngày'].unique(), reverse=True)
    selected_date = st.sidebar.selectbox("Chọn ngày cần xem:", list_days)

    if selected_date:
        # Lọc và sắp xếp theo thời gian để biểu đồ không bị trống/ngắt quãng
        filtered_df = df[df['Ngày'] == selected_date].sort_values('Thời gian')
        
        st.subheader(f"📅 Phân tích chi tiết ngày: {selected_date}")
        
        # 3. Khu vực Đánh giá thông số
        st.markdown("### 📝 Đánh giá chuyên sâu")
        c1, c2, c3, c4 = st.columns(4)

        with c1: # Ưu tiên Ánh sáng
            if 'soil_ASKK' in filtered_df.columns:
                val = filtered_df['soil_ASKK'].mean()
                if not pd.isna(val):
                    st.metric("Ánh sáng (Lux)", f"{val:.1f}")
                    if val > 15000: st.warning("☀️ Ánh sáng mạnh")
                    elif val < 5000: st.info("☁️ Ánh sáng yếu")
                    else: st.success("✅ Ánh sáng tối ưu")

        with c2: # Nhiệt độ & Độ ẩm
            t_col = 'tempKK' if 'tempKK' in filtered_df.columns else 'Nhiệt Độ'
            if t_col in filtered_df.columns:
                val_t = filtered_df[t_col].mean()
                if not pd.isna(val_t):
                    if val_t > 150: val_t = val_t / 10 # Sửa lỗi 331 -> 33.1
                    st.metric("Nhiệt độ (°C)", f"{val_t:.1f}")
                    if val_t > 35: st.error("🔥 Quá nóng!")
                    else: st.success("✅ Ổn định")

        with c3: # EC & PH (Cho file nhỏ giọt)
            ec_col = 'TBEC' if 'TBEC' in filtered_df.columns else 'EC'
            ph_col = 'TBPH' if 'TBPH' in filtered_df.columns else 'PH'
            
            if ec_col in filtered_df.columns:
                val_ec = filtered_df[ec_col].mean()
                if not pd.isna(val_ec) and val_ec > 0: st.metric("EC", f"{val_ec:.0f}")
                
            if ph_col in filtered_df.columns:
                val_ph = filtered_df[ph_col].mean()
                if not pd.isna(val_ph) and val_ph > 0:
                    if val_ph > 14: val_ph = val_ph / 100
                    st.metric("pH", f"{val_ph:.2f}")

        with c4: # Áp suất & Lưu lượng
            if 'AS_Value' in filtered_df.columns:
                val_as = filtered_df['AS_Value'].mean()
                if not pd.isna(val_as): st.metric("Áp suất (AS)", f"{val_as:.2f}")
            
            if 'Lưu lượng tổng' in filtered_df.columns:
                # Lấy giá trị lớn nhất trong ngày làm lưu lượng tổng
                st.metric("Lưu lượng tổng", f"{filtered_df['Lưu lượng tổng'].max():.1f}")

        # 4. Biểu đồ động
        st.subheader("📈 Biểu đồ diễn biến theo thời gian")
        
        # Tự động tìm các cột có dữ liệu thực tế (không bị trống hoàn toàn)
        numeric_cols = [c for c in cols_to_fix + ['AS_Value'] if c in filtered_df.columns and filtered_df[c].count() > 0]
        
        selected_metrics = st.multiselect(
            "Chọn thông số muốn xem biểu đồ:",
            options=numeric_cols,
            default=[numeric_cols[0]] if numeric_cols else []
        )
        
        if selected_metrics:
            # Làm sạch dữ liệu biểu đồ: loại bỏ dòng trắng của các cột đã chọn
            chart_df = filtered_df.set_index('Thời gian')[selected_metrics].dropna(how='all')
            st.line_chart(chart_df)
        else:
            st.warning("Vui lòng chọn thông số để hiển thị biểu đồ.")

        with st.expander("Xem bảng dữ liệu gốc"):
            st.write(filtered_df)
