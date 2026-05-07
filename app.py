import streamlit as st
import pandas as pd
import json
from datetime import timedelta

st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp", layout="wide")
st.title("🍀 Công cụ Phân tích Dữ liệu Nông nghiệp")

uploaded_file = st.file_uploader("Nạp tệp tin JSON của bạn", type=['json'])

def extract_value(val):
    if val is None or val == "" or val == "0": return None
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        if '/' in val:
            try:
                parts = val.strip().split(' ')
                last_part = parts[-1] 
                if '/' in last_part: return float(last_part.split('/')[-1])
            except: return None
        else:
            try: return float(val)
            except: return None
    return None

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)
        
        # 1. CHUẨN HÓA THỜI GIAN
        df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
        df = df.dropna(subset=['Thời gian']).sort_values('Thời gian')
        
        df['Ngày'] = df['Thời gian'].dt.date
        df['Tháng'] = df['Thời gian'].dt.to_period('M').astype(str)
        df['Năm_Col'] = df['Thời gian'].dt.year.astype(str)
        
        # 2. XỬ LÝ DỮ LIỆU CÁC CỘT
        exclude_cols = ['STT', 'Thời gian', 'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT']
        for col in df.columns:
            if col not in exclude_cols:
                df[col] = df[col].apply(extract_value)

        # 3. ĐỊNH DẠNG KHUNG THỜI GIAN
        df['Tuần_HT'] = df['Ngày'].apply(lambda x: f"Tuần ({(x - timedelta(days=x.weekday())).strftime('%d/%m')} - {(x - timedelta(days=x.weekday()) + timedelta(days=6)).strftime('%d/%m')})/{x.year}")
        df['Quý_HT'] = df['Thời gian'].apply(lambda dt: f"Quý {(dt.month - 1) // 3 + 1} (Tháng {((dt.month - 1) // 3)*3+1:02d} - {((dt.month - 1) // 3 + 1)*3:02d})/{dt.year}")
        df['Sáu_Tháng_HT'] = df['Thời gian'].apply(lambda dt: f"6 Tháng {'đầu' if dt.month <= 6 else 'cuối'} năm/{dt.year}")

        # 4. BỘ LỌC SIDEBAR
        st.sidebar.header("Cài đặt hiển thị")
        view_mode = st.sidebar.selectbox("Chọn chế độ xem:", ["Ngày", "Tuần", "Tháng", "Quý", "6 Tháng", "Năm"])

        filtered_df = pd.DataFrame()
        
        # Logic lọc (Rút gọn)
        map_col = {"Ngày": "Ngày", "Tuần": "Tuần_HT", "Tháng": "Tháng", "Quý": "Quý_HT", "6 Tháng": "Sáu_Tháng_HT", "Năm": "Năm_Col"}
        col_name = map_col[view_mode]
        targets = sorted(df[col_name].unique(), reverse=True)
        sel_label = st.sidebar.selectbox(f"Chọn {view_mode}:", targets)
        filtered_df = df[df[col_name] == sel_label].copy()

        # 5. HIỂN THỊ SỐ LIỆU TRUNG BÌNH
        if not filtered_df.empty:
            st.subheader(f"📊 Số liệu trung bình: {sel_label}")
            
            # --- HÀNG 1: CHỈ SỐ CƠ BẢN ---
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                t_col = next((c for c in ['Nhiệt Độ', 'tempKK', 'nhiệt độ EC'] if c in filtered_df.columns), None)
                if t_col:
                    t_val = filtered_df[t_col].mean()
                    if t_val > 150: t_val /= 10
                    st.metric("Nhiệt độ TB", f"{t_val:.1f} °C")
            with c2:
                ph_col = next((c for c in ['TBPH', 'PH', 'ph'] if c in filtered_df.columns), None)
                if ph_col: st.metric("PH trung bình", f"{filtered_df[ph_col].mean():.2f}")
            with c3:
                h_col = next((c for c in ['humiKK', 'Độ ẩm'] if c in filtered_df.columns), None)
                if h_col:
                    lbl = "Độ ẩm KK" if h_col == 'humiKK' else "Độ ẩm Đất"
                    st.metric(f"{lbl} TB", f"{filtered_df[h_col].mean():.1f} %")
            with c4:
                ec_col = next((c for c in ['TBEC', 'EC'] if c in filtered_df.columns), None)
                if ec_col: st.metric("EC trung bình", f"{filtered_df[ec_col].mean():.1f}")

            # --- HÀNG 2: CHỈ SỐ PHỤ & DINH DƯỠNG ---
            extra_metrics = {
                'AS': 'Áp suất (AS)', 'TDS EC': 'TDS EC', 'Điện trở suất EC': 'Điện trở suất',
                'Độ mặn EC': 'Độ mặn', 'Lưu lượng m2/h': 'Lưu lượng tức thời',
                'N': 'Nitơ (N)', 'P': 'Photpho (P)', 'K': 'Kali (K)'
            }
            available_extras = [col for col in extra_metrics.keys() if col in filtered_df.columns]
            
            if available_extras or ('Lưu lượng tổng' in filtered_df.columns):
                st.markdown("---")
                cols = st.columns(4)
                idx = 0
                # Hiện Nước tiêu thụ (Bản J)
                if 'Lưu lượng tổng' in filtered_df.columns:
                    v = filtered_df['Lưu lượng tổng'].dropna()
                    if not v.empty and v.max() > 0:
                        cols[idx % 4].metric("Nước đã dùng", f"{(v.max() - v.min()):.1f} m³")
                        idx += 1
                # Hiện các chỉ số khác
                for col in available_extras:
                    val = filtered_df[col].mean()
                    if pd.notnull(val):
                        cols[idx % 4].metric(extra_metrics[col], f"{val:.2f}")
                        idx += 1

            # 6. BIỂU ĐỒ
            st.subheader("📈 Biểu đồ diễn biến")
            numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
            chart_metrics = [m for m in numeric_cols if m not in ['Lưu lượng tổng', 'STT']]
            
            selected_m = st.multiselect("Thêm thông số vào biểu đồ:", chart_metrics, 
                                        default=[chart_metrics[0]] if chart_metrics else [])
            
            if selected_m:
                if view_mode == "Ngày":
                    chart_data = filtered_df.set_index('Thời gian')[selected_m].sort_index()
                else:
                    chart_data = filtered_df.groupby('Ngày')[selected_m].mean().sort_index()
                st.line_chart(chart_data)

            with st.expander("🔍 Xem bảng dữ liệu chi tiết"):
                st.dataframe(filtered_df)
            st.success("✅ Hệ thống đang vận hành ổn định.")

    except Exception as e:
        st.error(f"⚠️ Lỗi: {e}")
