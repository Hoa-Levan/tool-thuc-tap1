import streamlit as st
import pandas as pd
import json
from datetime import timedelta

# Cấu hình trang và Giao diện
st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp Toàn diện", layout="wide")
st.title("🍀 Công cụ Phân tích Dữ liệu Nông nghiệp")

# SỬA LỖI 1: Cho phép nạp nhiều file
uploaded_files = st.file_uploader("Nạp các tệp tin JSON của bạn", type=['json'], accept_multiple_files=True)

# HÀM XỬ LÝ CHUỖI PHỨC TẠP
def extract_value(val):
    if val is None or val == "" or val == "0":
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        if '/' in val:
            try:
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

if uploaded_files:
    try:
        all_dfs = []
        for f in uploaded_files:
            temp_data = json.load(f)
            temp_df = pd.DataFrame(temp_data)
            temp_df['Nguồn'] = f.name 
            all_dfs.append(temp_df)
        
        df = pd.concat(all_dfs, ignore_index=True)

        # SỬA LỖI 2: Đưa bộ chọn app_mode lên trước khi lọc dữ liệu
        st.sidebar.header("Cấu hình hệ thống")
        app_mode = st.sidebar.radio("Chọn chế độ phân tích:", ["Xem chi tiết 1 file", "So sánh đối chiếu"])

        if app_mode == "Xem chi tiết 1 file":
            selected_file = st.sidebar.selectbox("Chọn file cần xem:", [f.name for f in uploaded_files])
            display_df = df[df['Nguồn'] == selected_file].copy()
        else:
            display_df = df.copy()

        # 1. CHUẨN HÓA THỜI GIAN
        display_df['Thời gian'] = pd.to_datetime(display_df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
        display_df = display_df.dropna(subset=['Thời gian']).sort_values('Thời gian')
        
        display_df['Ngày'] = display_df['Thời gian'].dt.date
        display_df['Tháng'] = display_df['Thời gian'].dt.to_period('M').astype(str)
        display_df['Năm_Col'] = display_df['Thời gian'].dt.year.astype(str)
        
        # 2. XỬ LÝ DỮ LIỆU TẤT CẢ CÁC CỘT
        exclude_cols = ['Thời gian', 'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT', 'STT', 'Nguồn']
        for col in display_df.columns:
            if col not in exclude_cols:
                display_df[col] = display_df[col].apply(extract_value)

        # 3. ĐỊNH DẠNG KHUNG THỜI GIAN
        display_df['Tuần_HT'] = display_df['Ngày'].apply(lambda x: f"Tuần ({(x - timedelta(days=x.weekday())).strftime('%d/%m')} - {(x - timedelta(days=x.weekday()) + timedelta(days=6)).strftime('%d/%m')})/{x.year}")
        display_df['Quý_HT'] = display_df['Thời gian'].apply(lambda dt: f"Quý {(dt.month - 1) // 3 + 1} (Tháng {((dt.month - 1) // 3)*3+1:02d} - {((dt.month - 1) // 3 + 1)*3:02d})/{dt.year}")
        display_df['Sáu_Tháng_HT'] = display_df['Thời gian'].apply(lambda dt: f"6 Tháng {'đầu' if dt.month <= 6 else 'cuối'} năm/{dt.year}")

        # 4. BỘ LỌC SIDEBAR
        st.sidebar.header("Cài đặt hiển thị")
        view_mode = st.sidebar.selectbox("Chọn chế độ xem:", ["Ngày", "Tuần", "Tháng", "Quý", "6 Tháng", "Năm"])

        filtered_df = pd.DataFrame()
        sel_label = ""

        # Logic lọc dữ liệu dựa trên view_mode (Dùng display_df làm gốc)
        if view_mode == "Ngày":
            targets = sorted(display_df['Ngày'].unique(), reverse=True)
            sel_label = st.sidebar.selectbox("Chọn ngày:", targets)
            filtered_df = display_df[display_df['Ngày'] == sel_label].copy()
        elif view_mode == "Tháng":
            targets = sorted(display_df['Tháng'].unique(), reverse=True)
            sel_label = st.sidebar.selectbox("Chọn tháng:", targets)
            filtered_df = display_df[display_df['Tháng'] == sel_label].copy()
        # ... (Bạn có thể thêm tiếp các elif cho Tuần, Quý, Năm tương tự)
        else:
            targets = sorted(display_df[f'{view_mode}_HT' if 'Tháng' not in view_mode else 'Tháng'].unique(), reverse=True) if view_mode != "Năm" else sorted(display_df['Năm_Col'].unique(), reverse=True)
            sel_label = st.sidebar.selectbox(f"Chọn {view_mode}:", targets)
            # Tạm thời gán để tránh lỗi nếu chưa viết hết elif
            if view_mode == "Năm": filtered_df = display_df[display_df['Năm_Col'] == sel_label].copy()
            elif view_mode == "Tuần": filtered_df = display_df[display_df['Tuần_HT'] == sel_label].copy()

        # 5. HIỂN THỊ SỐ LIỆU TRUNG BÌNH (Tự động thích ứng AH4 và J)
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
                h_col = next((c for c in ['humiKK', 'Độ ẩm'] if c in filtered_df.columns), None)
                if h_col:
                    label = "Độ ẩm KK" if h_col == 'humiKK' else "Độ ẩm Đất"
                    st.metric(f"{label} TB", f"{filtered_df[h_col].mean():.1f} %")
            with c3:
                ph_col = next((c for c in ['TBPH', 'PH', 'ph'] if c in filtered_df.columns), None)
                if ph_col: st.metric("PH trung bình", f"{filtered_df[ph_col].mean():.2f}")
            with c4:
                # KIỂM TRA BẢN J (Có lưu lượng) HOẶC AH4 (Hiện EC thay thế)
                has_water = False
                if 'Lưu lượng tổng' in filtered_df.columns:
                    v = filtered_df['Lưu lượng tổng'].dropna()
                    if not v.empty and v.max() > 0:
                        usage = v.max() - v.min()
                        st.metric("Nước đã dùng (Bản J)", f"{usage:.1f} m³")
                        has_water = True
                
                if not has_water:
                    ec_col = next((c for c in ['TBEC', 'EC'] if c in filtered_df.columns), None)
                    if ec_col: st.metric("EC trung bình", f"{filtered_df[ec_col].mean():.1f}")

            # --- HÀNG 2: CHỈ SỐ PHỤ VÀ DINH DƯỠNG ---
            extra_metrics = {
                'AS': 'Áp suất (AS)', 
                'TDS EC': 'TDS EC', 
                'Độ mặn EC': 'Độ mặn', 
                'Lưu lượng m2/h': 'Lưu lượng tức thời (J)', # Chỉ hiện ở bản J
                'N': 'Nitơ (N)', 'P': 'Photpho (P)', 'K': 'Kali (K)'
            }
            available_extras = [col for col in extra_metrics.keys() if col in filtered_df.columns]
            
            if available_extras:
                st.markdown("---")
                cols = st.columns(4)
                for i, col in enumerate(available_extras):
                    val = filtered_df[col].mean()
                    if pd.notnull(val):
                        cols[i % 4].metric(extra_metrics[col], f"{val:.2f}")

            # 6. BIỂU ĐỒ DIỄN BIẾN
            st.subheader("📈 Biểu đồ diễn biến")
            numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
            # Loại bỏ các cột không nên vẽ đường (số quá lớn hoặc định danh)
            chart_metrics = [m for m in numeric_cols if m not in ['Lưu lượng tổng', 'STT']]
            
            selected_m = st.multiselect("Thêm thông số biểu đồ:", chart_metrics, 
                                        default=[chart_metrics[0]] if chart_metrics else [])
            
            if selected_m:
                if app_mode == "So sánh đối chiếu" and len(selected_m) == 1:
                    target = selected_m[0]
                    # Pivot để so sánh AH4 vs J hoặc Lịch sử vs Quan trắc
                    chart_data = filtered_df.pivot_table(
                        index='Thời gian' if view_mode == "Ngày" else 'Ngày', 
                        columns='Nguồn', 
                        values=target,
                        aggfunc='mean'
                    ).sort_index()
                    if view_mode == "Ngày": chart_data = chart_data.interpolate()
                    st.info(f"💡 Đang so sánh thông số **{target}** giữa các tệp tin đã chọn")
                else:
                    if view_mode == "Ngày":
                        chart_data = filtered_df.set_index('Thời gian')[selected_m].sort_index().dropna(how='all')
                    else:
                        chart_data = filtered_df.groupby('Ngày')[selected_m].mean().dropna(how='all')
                
                st.line_chart(chart_data)
            with st.expander("🔍 Xem bảng dữ liệu chi tiết"):
                st.dataframe(filtered_df)
            st.success("✅ Hệ thống hoạt động ổn định.")

    except Exception as e:
        st.error(f"⚠️ Lỗi: {e}")
