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
        exclude_cols = ['STT', 'Thời gian', 'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT']
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

        # 5. HIỂN THỊ SỐ LIỆU TRUNG BÌNH
        if not filtered_df.empty:
            st.subheader(f"📊 Số liệu trung bình: {sel_label}")
            
            # --- HÀNG 1: CÁC CHỈ SỐ MÔI TRƯỜNG CƠ BẢN ---
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                # Hiện Nhiệt độ (tìm tất cả các loại nhiệt độ có thể có)
                t_col = next((c for c in ['Nhiệt Độ', 'tempKK', 'nhiệt độ EC', 'nhiệt độ PH'] if c in filtered_df.columns), None)
                if t_col:
                    t_val = filtered_df[t_col].mean()
                    if t_val > 150: t_val /= 10
                    st.metric("Nhiệt độ TB", f"{t_val:.1f} °C")
            with c2:
                # Hiện Độ ẩm (KK hoặc Đất)
                h_col = next((c for c in ['humiKK', 'Độ ẩm'] if c in filtered_df.columns), None)
                if h_col:
                    label = "Độ ẩm KK" if h_col == 'humiKK' else "Độ ẩm Đất"
                    st.metric(f"{label} TB", f"{filtered_df[h_col].mean():.1f} %")
            with c3:
                # Hiện PH (Ưu tiên TBPH nếu có, không thì PH)
                ph_col = next((c for c in ['TBPH', 'PH', 'ph'] if c in filtered_df.columns), None)
                if ph_col:
                    st.metric("PH trung bình", f"{filtered_df[ph_col].mean():.2f}")
            with c4:
                # Hiện EC (Ưu tiên TBEC nếu có, không thì EC)
                ec_col = next((c for c in ['TBEC', 'EC'] if c in filtered_df.columns), None)
                if ec_col:
                    st.metric("EC trung bình", f"{filtered_df[ec_col].mean():.1f}")

            # --- HÀNG 2: CÁC CHỈ SỐ RIÊNG BIỆT (TỰ ĐỘNG HIỆN NẾU CÓ) ---
            # Danh sách các cột đặc thù của từng file
            extra_metrics = {
                'AS': 'Áp suất (AS)',
                'TDS EC': 'TDS EC',
                'Điện trở suất EC': 'Điện trở suất',
                'Độ mặn EC': 'Độ mặn',
                'Lưu lượng m2/h': 'Lưu lượng tức thời',
                'N': 'Nitơ 👎',
                'P': 'Photpho (P)',
                'K': 'Kali (K)'
            }
            
            # Lọc ra những cột thực sự có trong file đang mở
            available_extras = [col for col in extra_metrics.keys() if col in filtered_df.columns]
            
            if available_extras or ('Lưu lượng tổng' in filtered_df.columns):
                st.markdown("---")
                # Tạo các cột động dựa trên số lượng chỉ số tìm thấy
                cols = st.columns(4) 
                idx = 0
                
                # Ưu tiên hiện "Nước đã dùng" nếu là file Lịch sử nhỏ giọt
                if 'Lưu lượng tổng' in filtered_df.columns:
                    v = filtered_df['Lưu lượng tổng'].dropna()
                    if not v.empty and v.max() > 0:
                        usage = v.max() - v.min()
                        cols[idx % 4].metric("Nước đã dùng", f"{usage:.1f} m³")
                        idx += 1
                
                # Hiện tất cả các chỉ số phụ khác (AS, TDS, Độ mặn, NPK...)
                for col in available_extras:
                    val = filtered_df[col].mean()
                    if pd.notnull(val):
                        cols[idx % 4].metric(extra_metrics[col], f"{val:.2f}")
                        idx += 1
                        # Nếu vượt quá 4 chỉ số, Streamlit sẽ tự động tràn hàng nếu ta xử lý khéo, 
                        # ở đây ta dùng idx % 4 để quay vòng trong 4 cột.

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
