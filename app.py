import streamlit as st
import pandas as pd
import json
from datetime import timedelta

st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp", layout="wide")
st.title("📊 Phân tích Dữ liệu Nông nghiệp Đa khung thời gian")

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
    
    df['Ngày'] = df['Thời gian'].dt.date
    df['Tháng'] = df['Thời gian'].dt.to_period('M').astype(str)
    df['Năm'] = df['Thời gian'].dt.year.astype(str)
    
    # Định dạng Tuần
    def get_week_range(date):
        start = date - timedelta(days=date.weekday())
        end = start + timedelta(days=6)
        return f"Tuần ({start.strftime('%d/%m')} - {end.strftime('%d/%m')})/{start.year}"
    df['Tuần_HT'] = df['Thời gian'].dt.date.apply(get_week_range)

    # Định dạng Quý
    def get_quarter_range(dt):
        q = (dt.month - 1) // 3 + 1
        return f"Quý {q} (Tháng {(q-1)*3+1:02d} - Tháng {q*3:02d})/{dt.year}"
    df['Quý_HT'] = df['Thời gian'].apply(get_quarter_range)

    # Định dạng 6 Tháng (Bán niên)
    def get_half_year(dt):
        if dt.month <= 6:
            return f"6 Tháng đầu năm (Tháng 01 - Tháng 06)/{dt.year}"
        else:
            return f"6 Tháng cuối năm (Tháng 07 - Tháng 12)/{dt.year}"
    df['Sáu_Tháng_HT'] = df['Thời gian'].apply(get_half_year)

    # Ép kiểu số
    cols_to_fix = ['soil_ASKK', 'Nhiệt Độ', 'Độ ẩm', 'Lưu lượng m2/h', 'Lưu lượng tổng', 'tempKK', 'humiKK', 'EC', 'PH', 'TBEC', 'TBPH']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'AS' in df.columns:
        df['AS_Value'] = df['AS'].apply(lambda x: pd.to_numeric(x, errors='coerce') if '/' not in str(x) else parse_time_series(x))

    # 2. BỘ LỌC
    st.sidebar.header("Cài đặt hiển thị")
    view_mode = st.sidebar.selectbox("Chọn chế độ xem:", ["Ngày", "Tuần", "Tháng", "Quý", "6 Tháng", "Năm"])

    if view_mode == "Ngày":
        targets = sorted(df['Ngày'].unique(), reverse=True)
        selected = st.sidebar.selectbox("Chọn ngày:", targets)
        filtered_df = df[df['Ngày'] == selected]
    elif view_mode == "Tuần":
        order = df.groupby('Tuần_HT')['Thời gian'].min().sort_values(ascending=False).index
        selected = st.sidebar.selectbox("Chọn tuần:", order)
        filtered_df = df[df['Tuần_HT'] == selected]
    elif view_mode == "Tháng":
        targets = sorted(df['Tháng'].unique(), reverse=True)
        selected = st.sidebar.selectbox("Chọn tháng:", targets)
        filtered_df = df[df['Tháng'] == selected]
    elif view_mode == "Quý":
        order = df.groupby('Quý_HT')['Thời gian'].min().sort_values(ascending=False).index
        selected = st.sidebar.selectbox("Chọn quý:", order)
        filtered_df = df[df['Quý_HT'] == selected]
    elif view
