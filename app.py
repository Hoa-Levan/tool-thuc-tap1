import streamlit as st
import pandas as pd
import json
from datetime import timedelta

st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp", layout="wide")
st.title("📊 Phân tích Dữ liệu Nông nghiệp")

uploaded_file = st.file_uploader("Nạp tệp tin JSON của bạn", type=['json'])

def parse_time_series(value):
    if not value or value == "0" or not isinstance(value, str):
        return None
    try:
        parts = value.strip().split(' ')
        last_val = parts[-1].split('/')[-1]
        return float(last_val)
    except:
        return None

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)
        
        # 1. CHUẨN HÓA THỜI GIAN
        df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
        df = df.dropna(subset=['Thời gian']).sort_values('Thời gian')
        
        # Tạo các cột phân loại thời gian ngay từ đầu để tránh lỗi KeyError
        df['Ngày'] = df['Thời gian'].dt.date
        df['Tháng'] = df['Thời gian'].dt.to_period('M').astype(str)
        df['Năm_Col'] = df['Thời gian'].dt.year.astype(str) # Dùng tên cột riêng để tránh trùng với hàm của hệ thống
        
        def get_week_range(date):
            start = date - timedelta(days=date.weekday())
            end = start + timedelta(days=6)
            return f"Tuần ({start.strftime('%d/%m')} - {end.strftime('%d/%m')})/{start.year}"
        df['Tuần_HT'] = df['Ngày'].apply(get_week_range)

        def get_quarter_range(dt):
            q = (dt.month - 1) // 3 + 1
            return f"Quý {q} (Tháng {(q-1)*3+1:02d} - Tháng {q*3:02d})/{dt.year}"
        df['Quý_HT'] = df['Thời gian'].apply(get_quarter_range)

        def get_half_year(dt):
            if dt.month <= 6:
                return f"6 Tháng đầu năm (Tháng 01 - Tháng 06)/{dt.year}"
            else:
                return f"6 Tháng cuối năm (Tháng 07 - Tháng 12)/{dt.year}"
        df['Sáu_Tháng_HT'] = df['Thời gian'].apply(get_half_year)

        # 2. CHUẨN HÓA SỐ LIỆU
        cols_to_fix = ['soil_ASKK', 'Nhiệt Độ', 'Độ ẩm', 'Lưu lượng m2/h', 'Lưu lượng tổng', 'tempKK', 'humiKK', 'EC', 'PH', 'TBEC', 'TBPH']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'AS' in df.columns:
            df['AS_Value'] = df['AS'].apply(lambda x: pd.to_numeric(x, errors='coerce') if '/' not in str(x) else parse_time_series(x))

        # 3. BỘ LỌC CẢI TIẾN
        st.sidebar.header("Cài đặt hiển thị")
        view_mode = st.sidebar.selectbox("Chọn chế độ xem:", ["Ngày", "Tuần", "Tháng", "Quý", "6 Tháng", "Năm"])

        filtered_df = pd.DataFrame()
        sel_label = ""

        if view_mode == "Ngày":
            targets = sorted(df['Ngày'].unique(), reverse=True)
            sel_label = st.sidebar.selectbox("Chọn ngày:", targets)
            filtered_df = df[df['Ngày'] == sel_label].copy()
        elif view_mode == "Tuần":
            order = df.groupby('Tuần_HT')['Thời gian'].min().sort_values(ascending=False).index
            sel_label = st.sidebar.selectbox("Chọn tuần:", order)
            filtered_df = df[df['Tuần_HT'] == sel_label].copy()
        elif view_mode == "Tháng":
            targets = sorted(df['Tháng'].unique(), reverse=True)
            sel_label = st.sidebar.selectbox("Chọn tháng:", targets)
            filtered_df = df[df['Tháng'] == sel_label].copy()
        elif view_mode == "Quý":
            order = df.groupby('Quý_HT')['Thời gian'].min().sort_values(ascending=False).index
            sel_label = st.sidebar.selectbox("Chọn quý:", order)
            filtered_df = df[df['Quý_HT'] == sel_label].copy()
        elif view_mode == "6 Tháng":
            order = df.groupby('Sáu_Tháng_HT')['Thời gian'].min().sort_values(ascending=False).index
            sel_label = st.sidebar.selectbox("Chọn giai đoạn:", order)
            filtered_df = df[df['Sáu_Tháng_HT'] == sel_label].copy()
        elif view_mode == "Năm":
            targets = sorted(df['Năm_Col'].unique(), reverse=True) # Sửa lỗi chọn Năm
            sel_label = st.sidebar.selectbox("Chọn năm:", targets)
            filtered_df = df[df['Năm_Col'] == sel_label].copy()

        # 4. HIỂN THỊ CHỈ SỐ
        if not filtered_df.empty:
            st.subheader(f"📅 Báo cáo: {sel_label}")
            
            # Xử lý Nước đã dùng (Chống lỗi nan m3 trong hình của bạn)
            usage = 0.0
            if 'Lưu lượng tổng' in filtered_df.columns:
                valid_usage = filtered_df['Lưu lượng tổng'].dropna()
                if not valid_usage.empty:
                    usage = valid_usage.max() - valid_usage.min()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if 'soil_ASKK' in filtered_df.columns:
                    st.metric("Ánh sáng TB", f"{filtered_df['soil_ASKK'].mean():.1f} Lux")
            with c2:
                t_col = 'tempKK' if 'tempKK' in filtered_df.columns else 'Nhiệt Độ'
                if t_col in filtered_df.columns:
                    t_val = filtered_df[t_col].mean()
                    if t_val > 150: t_val /= 10
                    st.metric("Nhiệt độ TB", f"{t_val:.1f} °C")
            with c3:
                ec_col = 'TBEC' if 'TBEC' in filtered_df.columns else 'EC'
                if ec_col in filtered_df.columns:
                    st.metric("EC TB", f"{filtered_df[ec_col].mean():.1f}")
            with c4:
                st.metric("Nước đã dùng", f"{max(0, usage):.1f} m³")

            # 5. BIỂU ĐỒ DIỄN BIẾN
            st.subheader("📈 Biểu đồ xu hướng diễn biến")
            metrics = [c for c in cols_to_fix + ['AS_Value'] if c in filtered_df.columns and filtered_df[c].count() > 0]
            selected_m = st.multiselect("Chọn thông số:", metrics, default=[metrics[0]] if metrics else [])
            
            if selected_m:
                if view_mode == "Ngày":
                    # Để hiện đường kẻ: Sắp xếp theo thời gian và loại bỏ các dòng rỗng xen kẽ
                    chart_data = filtered_df.set_index('Thời gian')[selected_m].sort_index().dropna(how='all')
                else:
                    # Các chế độ dài hạn: Gom theo Ngày để nối các điểm lại thành đường
                    chart_data = filtered_df.groupby('Ngày')[selected_m].mean().dropna(how='all')
                
                st.line_chart(chart_data)

            with st.expander("Bảng dữ liệu chi tiết"):
                st.dataframe(filtered_df)

    except Exception as e:
        st.error(f"⚠️ Đã xảy ra lỗi khi xử lý dữ liệu: {e}")
