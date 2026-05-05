import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Hệ thống Phân tích Đa năng", layout="wide")
st.title("📊 Phân tích Dữ liệu Nông nghiệp (Đa khung thời gian)")

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
    data = json.load(uploaded_file)
    df = pd.DataFrame(data)
    
    # 1. Chuẩn hóa dữ liệu & Thời gian
    df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
    df = df.dropna(subset=['Thời gian']).sort_values('Thời gian')
    
    # Tạo các cột thời gian bổ sung
    df['Ngày'] = df['Thời gian'].dt.date
    df['Tuần'] = df['Thời gian'].dt.isocalendar().week
    df['Tháng'] = df['Thời gian'].dt.to_period('M').astype(str)
    df['Quý'] = df['Thời gian'].dt.to_period('Q').astype(str)
    df['Năm'] = df['Thời gian'].dt.year.astype(str)
    
    # Ép kiểu số an toàn
    cols_to_fix = ['soil_ASKK', 'Nhiệt Độ', 'Độ ẩm', 'Lưu lượng m2/h', 'Lưu lượng tổng', 'tempKK', 'humiKK', 'EC', 'PH', 'TBEC', 'TBPH']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'AS' in df.columns:
        df['AS_Value'] = df['AS'].apply(lambda x: pd.to_numeric(x, errors='coerce') if '/' not in str(x) else parse_time_series(x))

    # 2. BỘ LỌC ĐA KHUNG THỜI GIAN
    st.sidebar.header("Cài đặt hiển thị")
    view_mode = st.sidebar.selectbox("Chọn chế độ xem:", ["Ngày", "Tuần", "Tháng", "Quý", "Năm"])

    if view_mode == "Ngày":
        target_list = sorted(df['Ngày'].unique(), reverse=True)
        selected = st.sidebar.selectbox("Chọn ngày:", target_list)
        filtered_df = df[df['Ngày'] == selected]
    elif view_mode == "Tuần":
        target_list = sorted(df['Tuần'].unique(), reverse=True)
        selected = st.sidebar.selectbox("Chọn số tuần (trong năm):", target_list)
        filtered_df = df[df['Tuần'] == selected]
    elif view_mode == "Tháng":
        target_list = sorted(df['Tháng'].unique(), reverse=True)
        selected = st.sidebar.selectbox("Chọn tháng:", target_list)
        filtered_df = df[df['Tháng'] == selected]
    elif view_mode == "Quý":
        target_list = sorted(df['Quý'].unique(), reverse=True)
        selected = st.sidebar.selectbox("Chọn quý:", target_list)
        filtered_df = df[df['Quý'] == selected]
    else: # Năm
        target_list = sorted(df['Năm'].unique(), reverse=True)
        selected = st.sidebar.selectbox("Chọn năm:", target_list)
        filtered_df = df[df['Năm'] == selected]

    if not filtered_df.empty:
        st.subheader(f"📅 Báo cáo dữ liệu theo {view_mode}: {selected}")
        
        # 3. Đánh giá trung bình trong giai đoạn này
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if 'soil_ASKK' in filtered_df.columns:
                st.metric("Ánh sáng TB", f"{filtered_df['soil_ASKK'].mean():.1f}")
        with c2:
            t_col = 'tempKK' if 'tempKK' in filtered_df.columns else 'Nhiệt Độ'
            if t_col in filtered_df.columns:
                t_val = filtered_df[t_col].mean()
                if t_val > 150: t_val /= 10
                st.metric("Nhiệt độ TB", f"{t_val:.1f} °C")
        with c3:
            ec_col = 'TBEC' if 'TBEC' in filtered_df.columns else 'EC'
            if ec_col in filtered_df.columns:
                st.metric("EC trung bình", f"{filtered_df[ec_col].mean():.1f}")
        with c4:
            if 'Lưu lượng tổng' in filtered_df.columns:
                total_usage = filtered_df['Lưu lượng tổng'].max() - filtered_df['Lưu lượng tổng'].min()
                st.metric("Lượng nước đã dùng", f"{total_usage:.1f}")

        # 4. Biểu đồ diễn biến
        st.subheader(f"📈 Biểu đồ xu hướng trong {view_mode.lower()}")
        
        metrics = [c for c in cols_to_fix + ['AS_Value'] if c in filtered_df.columns and filtered_df[c].count() > 0]
        selected_m = st.multiselect("Chọn thông số xem xu hướng:", metrics, default=[metrics[0]] if metrics else [])
        
        if selected_m:
            # Nếu xem theo giai đoạn dài, ta sẽ lấy giá trị trung bình theo từng ngày để biểu đồ dễ nhìn
            if view_mode != "Ngày":
                chart_data = filtered_df.groupby('Ngày')[selected_m].mean()
            else:
                chart_data = filtered_df.set_index('Thời gian')[selected_m]
            
            st.line_chart(chart_data)

        with st.expander("Xem chi tiết dữ liệu"):
            st.dataframe(filtered_df)
