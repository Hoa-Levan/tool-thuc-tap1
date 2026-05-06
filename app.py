import streamlit as st
import pandas as pd
import json
from datetime import timedelta

# Cấu hình trang và Giao diện
st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp Toàn diện", layout="wide")
st.title("🍀 Công cụ Phân tích Dữ liệu Nông nghiệp")

uploaded_file = st.file_uploader("Nạp tệp tin JSON của bạn", type=['json'])

# HÀM XỬ LÝ CHUỖI PHỨC TẠP: Tách giá trị đứng sau dấu "/"
def extract_value(val):
    if val is None or val == "" or val == "0":
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        if '/' in val:
            try:
                # Tách lấy cụm cuối cùng trong chuỗi và lấy số sau dấu /
                parts = val.strip().split(' ')
                last_part = parts[-1] 
                if '/' in last_part:
                    return float(last_part.split('/')[-1])
            except:
                return None
        else:
            try:
                return float(val)
            except:
                return None
    return None

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)
        
        # 1. CHUẨN HÓA THỜI GIAN
        df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
        df = df.dropna(subset=['Thời gian']).sort_values('Thời gian')
        
        # Tạo cột phân loại thời gian
        df['Ngày'] = df['Thời gian'].dt.date
        df['Tháng'] = df['Thời gian'].dt.to_period('M').astype(str)
        df['Năm_Col'] = df['Thời gian'].dt.year.astype(str)
        
        # 2. XỬ LÝ DỮ LIỆU TẤT CẢ CÁC CỘT (Ép kiểu số & Tách dấu /)
        exclude_cols = ['Thời gian', 'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT']
        for col in df.columns:
            if col not in exclude_cols:
                df[col] = df[col].apply(extract_value)

        # 3. ĐỊNH DẠNG KHUNG THỜI GIAN HIỂN THỊ
        df['Tuần_HT'] = df['Ngày'].apply(lambda x: f"Tuần ({(x - timedelta(days=x.weekday())).strftime('%d/%m')} - {(x - timedelta(days=x.weekday()) + timedelta(days=6)).strftime('%d/%m')})/{x.year}")
        df['Quý_HT'] = df['Thời gian'].apply(lambda dt: f"Quý {(dt.month - 1) // 3 + 1} (Tháng {((dt.month - 1) // 3)*3+1:02d} - {((dt.month - 1) // 3 + 1)*3:02d})/{dt.year}")
        df['Sáu_Tháng_HT'] = df['Thời gian'].apply(lambda dt: f"6 Tháng {'đầu' if dt.month <= 6 else 'cuối'} năm/{dt.year}")

        # 4. BỘ LỌC SIDEBAR
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
        else:
            targets = sorted(df['Năm_Col'].unique(), reverse=True)
            sel_label = st.sidebar.selectbox("Chọn năm:", targets)
            filtered_df = df[df['Năm_Col'] == sel_label].copy()

        # 5. HIỂN THỊ CHỈ SỐ TỔNG HỢP (METRICS)
        if not filtered_df.empty:
            st.subheader(f"📝 Đánh giá chuyên sâu: {sel_label}")
            
            # Tính toán thông minh cho các chỉ số quan trọng
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                col_as = 'AS' if 'AS' in filtered_df.columns else None
                if col_as: st.metric("Áp suất (AS) TB", f"{filtered_df[col_as].mean():.2f}")
            with c2:
                t_col = next((c for c in ['Nhiệt Độ', 'tempKK', 'nhiệt độ EC'] if c in filtered_df.columns), None)
                if t_col:
                    t_val = filtered_df[t_col].mean()
                    if t_val > 150: t_val /= 10 # Hiệu chỉnh lỗi hiển thị số lớn
                    st.metric("Nhiệt độ TB", f"{t_val:.1f} °C")
            with c3:
                ec_col = next((c for c in ['TBEC', 'EC'] if c in filtered_df.columns), None)
                if ec_col: st.metric("EC TB", f"{filtered_df[ec_col].mean():.1f}")
            with c4:
                usage = 0.0
                if 'Lưu lượng tổng' in filtered_df.columns:
                    v = filtered_df['Lưu lượng tổng'].dropna()
                    if not v.empty: usage = v.max() - v.min()
                st.metric("Nước đã dùng", f"{max(0, usage):.1f} m³")

            # 6. BIỂU ĐỒ DIỄN BIẾN THEO THỜI GIAN
            st.subheader("📈 Biểu đồ diễn biến")
            
            # Lấy tất cả cột số trừ cột 'Lưu lượng tổng' (vì số quá lớn làm lệch biểu đồ)
            numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
            chart_metrics = [m for m in numeric_cols if m not in ['Lưu lượng tổng']]
            
            selected_m = st.multiselect("Bấm vào đây để thêm thông số (PH, TDS, Độ mặn, Nhiệt độ...):", 
                                        chart_metrics, 
                                        default=[chart_metrics[0]] if chart_metrics else [])
            
            if selected_m:
                if view_mode == "Ngày":
                    # Đảm bảo nối đường cho biểu đồ ngày
                    chart_data = filtered_df.set_index('Thời gian')[selected_m].sort_index().dropna(how='all')
                else:
                    # Gom nhóm theo ngày cho các chế độ dài hạn
                    chart_data = filtered_df.groupby('Ngày')[selected_m].mean().dropna(how='all')
                
                st.line_chart(chart_data)

            # 7. CHI TIẾT DỮ LIỆU
            with st.expander("🔍 Xem bảng dữ liệu chi tiết"):
                st.dataframe(filtered_df)
                
            # Thông báo trạng thái vận hành
            st.success("✅ Hệ thống đang vận hành và cập nhật dữ liệu liên tục.")

    except Exception as e:
        st.error(f"⚠️ Đã xảy ra lỗi: {e}")
