import streamlit as st
import pandas as pd
import json
import re

st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu Nông nghiệp")

# Hàm xử lý số liệu "vạn năng"
def clean_numeric(x):
    if pd.isna(x) or x == "": return None
    if isinstance(x, (int, float)): return float(x)
    try:
        # Nếu là dạng chuỗi 'thời gian/giá trị' (VD: 16-01-59/33.09)
        if '/' in str(x):
            parts = str(x).strip().split(' ')
            last_part = parts[-1].split('/')[-1]
            return float(last_part)
        # Nếu là chuỗi số thuần túy
        return float(str(x).replace(',', ''))
    except:
        return None

uploaded_file = st.file_uploader("Nạp tệp tin JSON", type=['json'])

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)
        
        # 1. XỬ LÝ THỜI GIAN
        df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
        df = df.dropna(subset=['Thời gian']).sort_values('Thời gian')
        df['Ngày'] = df['Thời gian'].dt.date

        # 2. CHUẨN HÓA DỮ LIỆU
        # Danh sách tất cả các cột có thể có
        cols_to_clean = ['soil_ASKK', 'tempKK', 'humiKK', 'AS', 'Lưu lượng m2/h', 
                         'Lưu lượng tổng', 'EC', 'PH', 'Nhiệt Độ', 'Độ ẩm', 'TBEC', 'TBPH']
        
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        # Sửa lỗi nhiệt độ (331 -> 33.1)
        for t_col in ['Nhiệt Độ', 'tempKK']:
            if t_col in df.columns:
                df[t_col] = df[t_col].apply(lambda x: x/10 if (x is not None and x > 150) else x)

        # 3. BỘ LỌC NGÀY
        st.sidebar.header("Bộ lọc")
        list_days = sorted(df['Ngày'].unique(), reverse=True)
        selected_date = st.sidebar.selectbox("Chọn ngày:", list_days)
        filtered_df = df[df['Ngày'] == selected_date].copy()

        # 4. HIỂN THỊ ĐÁNH GIÁ
        st.subheader(f"📝 Chỉ số trung bình ngày {selected_date}")
        c1, c2, c3, c4 = st.columns(4)

        with c1: # Ánh sáng
            val_as = filtered_df['soil_ASKK'].mean() if 'soil_ASKK' in filtered_df.columns else None
            if val_as is not None:
                st.metric("Ánh sáng (Lux)", f"{val_as:.1f}")
                if val_as > 10000: st.warning("☀️ Mạnh")
                elif val_as < 2000: st.info("☁️ Yếu")
                else: st.success("✅ Đủ")

        with c2: # Nhiệt độ & Độ ẩm
            t_val = filtered_df['tempKK'].mean() if 'tempKK' in filtered_df.columns else filtered_df['Nhiệt Độ'].mean()
            if not pd.isna(t_val): st.metric("Nhiệt độ", f"{t_val:.1f} °C")
            h_val = filtered_df['humiKK'].mean() if 'humiKK' in filtered_df.columns else filtered_df['Độ ẩm'].mean()
            if not pd.isna(h_val): st.metric("Độ ẩm", f"{h_val:.1f} %")

        with c3: # Hóa lý (EC/PH)
            # Ưu tiên cột TB (Trung bình) nếu có
            ec = filtered_df['TBEC'].mean() if 'TBEC' in filtered_df.columns else filtered_df['EC'].mean()
            ph = filtered_df['TBPH'].mean() if 'TBPH' in filtered_df.columns else filtered_df['PH'].mean()
            if ec > 0: st.metric("EC", f"{ec:.0f}")
            if ph > 0:
                if ph > 14: ph = ph / 100
                st.metric("pH", f"{ph:.2f}")

        with c4: # Áp suất & Lưu lượng
            pres = filtered_df['AS'].mean() if 'AS' in filtered_df.columns else None
            if pres is not None: st.metric("Áp suất (AS)", f"{pres:.2f}")
            total_f = filtered_df['Lưu lượng tổng'].max() if 'Lưu lượng tổng' in filtered_df.columns else None
            if total_f is not None: st.metric("Lưu lượng tổng", f"{total_f:.1f}")

        # 5. BIỂU ĐỒ DIỄN BIẾN
        st.subheader("📈 Biểu đồ diễn biến")
        # Chỉ hiện những cột có dữ liệu thực sự
        active_cols = [c for c in cols_to_clean if c in filtered_df.columns and filtered_df[c].count() > 0]
        
        selected = st.multiselect("Chọn thông số muốn xem:", active_cols, default=active_cols[:1] if active_cols else [])
        
        if selected:
            # Sửa lỗi biểu đồ trống: tạo df mới chỉ gồm thời gian và các cột chọn
            chart_data = filtered_df[['Thời gian'] + selected].set_index('Thời gian')
            st.line_chart(chart_data)

        with st.expander("Dữ liệu chi tiết"):
            st.dataframe(filtered_df)

    except Exception as e:
        st.error(f"⚠️ Có lỗi xảy ra: {e}")
