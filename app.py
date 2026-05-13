import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import timedelta
from hourly_logic import handle_hourly_view
from display_logic import get_chart_data
from zone_logic import handle_zone_selection
from bomvan_logic import process_device_columns
from control_logic import init_control_state, render_confirm_button, should_load

# Cấu hình trang và Giao diện
st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp Toàn diện", layout="wide")
st.title("🍀 Công cụ Phân tích Dữ liệu Nông nghiệp")
init_control_state()

uploaded_file = st.file_uploader("Nạp tệp tin JSON của bạn", type=['json'])

# HÀM XỬ LÝ CHUỖI PHỨC TẠP: Tách giá trị đứng sau dấu "/"
def extract_value(val):
    if pd.isna(val) or val == "": 
        return 0.0
    
    val_str = str(val).strip()
    
    # Xử lý trường hợp có dấu '/' (như EC/PH hoặc lỗi định dạng rác)
    if "/" in val_str:
        try:
            # Chỉ lấy phần tử cuối cùng sau dấu gạch chéo
            parts = val_str.split('/')
            return float(parts[-1])
        except:
            return 0.0
            
    # Xử lý trường hợp số thuần túy
    try:
        return float(val_str)
    except:
        return 0.0

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
        df = process_device_columns(df)
        
        # 2. XỬ LÝ DỮ LIỆU TẤT CẢ CÁC CỘT (Ép kiểu số & Tách dấu /)
        exclude_cols = ['STT', 'Thời gian', 'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT', 'Tên khu', 'Trạng thái', 'Phương thức hoạt động', 'Người điều khiển', 'Bơm', 'Van']
        for col in df.columns:
            if col not in exclude_cols:
                df[col] = df[col].apply(extract_value)

        # 3. ĐỊNH DẠNG KHUNG THỜI GIAN HIỂN THỊ
        df['Tuần_HT'] = df['Ngày'].apply(lambda x: f"Tuần ({(x - timedelta(days=x.weekday())).strftime('%d/%m')} - {(x - timedelta(days=x.weekday()) + timedelta(days=6)).strftime('%d/%m')})/{x.year}")
        df['Quý_HT'] = df['Thời gian'].apply(lambda dt: f"Quý {(dt.month - 1) // 3 + 1} (Tháng {((dt.month - 1) // 3)*3+1:02d} - {((dt.month - 1) // 3 + 1)*3:02d})/{dt.year}")
        df['Sáu_Tháng_HT'] = df['Thời gian'].apply(lambda dt: f"6 Tháng {'đầu' if dt.month <= 6 else 'cuối'} năm/{dt.year}")

        # --- 4. BỘ LỌC SIDEBAR ---
        with st.sidebar:
            st.header("🔍 Bộ lọc dữ liệu")
            
            # Sử dụng Form để bao bọc tất cả bộ lọc, ngăn tự động load khi chỉnh ngày/giờ
            with st.form("sidebar_filter_form"):
                view_mode = st.selectbox(
                    "Chọn chế độ xem:", 
                    ["Ngày", "Xem theo Giờ", "Tuần", "Tháng", "Quý", "6 Tháng", "Năm"],
                    key="main_view_mode" # Thêm key để sửa lỗi Duplicate ID
                )
                
                filtered_df = pd.DataFrame()
                sel_label = ""
    
                # Logic hiển thị bộ chọn dựa trên view_mode (Giữ nguyên toàn bộ logic cũ)
                if view_mode == "Xem theo Giờ":
                    filtered_df, sel_label = handle_hourly_view(df)
                    
                elif view_mode == "Ngày":
                    targets = sorted(df['Ngày'].unique(), reverse=True)
                    sel_label = st.selectbox("Chọn ngày:", targets, key="day_select")
                    filtered_df = df[df['Ngày'] == sel_label].copy()
                    
                elif view_mode == "Tuần":
                    order = df.groupby('Tuần_HT')['Thời gian'].min().sort_values(ascending=False).index
                    sel_label = st.selectbox("Chọn tuần:", order, key="week_select")
                    filtered_df = df[df['Tuần_HT'] == sel_label].copy()
                    
                elif view_mode == "Tháng":
                    order = df.groupby('Tháng')['Thời gian'].min().sort_values(ascending=False).index
                    sel_label = st.selectbox("Chọn tháng:", order, key="month_select")
                    filtered_df = df[df['Tháng'] == sel_label].copy()
                    
                elif view_mode == "Quý":
                    order = df.groupby('Quý_HT')['Thời gian'].min().sort_values(ascending=False).index
                    sel_label = st.selectbox("Chọn quý:", order, key="quarter_select")
                    filtered_df = df[df['Quý_HT'] == sel_label].copy()
                    
                elif view_mode == "6 Tháng":
                    order = df.groupby('Sáu_Tháng_HT')['Thời gian'].min().sort_values(ascending=False).index
                    sel_label = st.selectbox("Chọn giai đoạn 6 tháng:", order, key="sixmonth_select")
                    filtered_df = df[df['Sáu_Tháng_HT'] == sel_label].copy()
                    
                elif view_mode == "Năm":
                    targets = sorted(df['Năm_Col'].unique(), reverse=True)
                    sel_label = st.selectbox("Chọn năm:", targets, key="year_select")
                    filtered_df = df[df['Năm_Col'] == sel_label].copy()

                # --- KHOẢNG CÁCH NGĂN CÁCH ---
                st.markdown("---")
                
                # --- NHÓM 2: TÙY CHỈNH BIỂU ĐỒ ---
                st.markdown("### 🎨 Tùy chỉnh biểu đồ")
                display_type = st.radio(
                    "Kiểu hiển thị số liệu:",
                    ["Số liệu trung bình cộng", "Số liệu thô"],
                    help="Chọn 'Mỗi lần đo' để xem chi tiết dữ liệu gốc (ô rỗng sẽ hiện là 0).",
                    key="display_type_radio"
                )
                
                # Nút Submit của Form - Sửa lỗi Missing Submit Button
                submitted = st.form_submit_button("🔥 XÁC NHẬN VÀ TẢI DỮ LIỆU", use_container_width=True)

        # 5. HIỂN THỊ DỮ LIỆU (Chỉ chạy khi đã nhấn nút xác nhận)
        if submitted:
            # Xử lý chọn khu vực
            filtered_df, current_zone, column_order = handle_zone_selection(df, filtered_df)
            
            # Đánh dấu trạng thái đã xác nhận để logic control hoạt động
            st.session_state.is_confirmed = True

        # Sử dụng logic should_load() để bao bọc phần hiển thị chính
        if should_load():
            if not filtered_df.empty:
                display_label = sel_label if current_zone == "Tất cả" else f"Tất cả lịch sử khu {current_zone}"
                st.subheader(f"📊 Số liệu trung bình: {display_label}")
                
                # --- HÀNG 1: CÁC CHỈ SỐ MÔI TRƯỜNG CƠ BẢN (Logic cũ nguyên bản) ---
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    t_col = next((c for c in ['Nhiệt Độ', 'tempKK', 'nhiệt độ EC', 'nhiệt độ PH'] if c in filtered_df.columns), None)
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
                    if ph_col:
                        st.metric("PH trung bình", f"{filtered_df[ph_col].mean():.2f}")
                with c4:
                    ec_col = next((c for c in ['TBEC', 'EC'] if c in filtered_df.columns), None)
                    if ec_col:
                        st.metric("EC trung bình", f"{filtered_df[ec_col].mean():.1f}")
        
                # --- HÀNG 2: CÁC CHỈ SỐ RIÊNG BIỆT (Logic cũ nguyên bản) ---
                extra_metrics = {
                    'AS': 'Áp suất (AS)',
                    'TDS EC': 'TDS EC',
                    'Điện trở suất EC': 'Điện trở suất',
                    'Độ mặn EC': 'Độ mặn',
                    'Lưu lượng m2/h': 'Lưu lượng tức thời',
                    'N': 'Nitơ (N)',
                    'P': 'Photpho (P)',
                    'K': 'Kali (K)'
                }
                
                available_extras = [col for col in extra_metrics.keys() if col in filtered_df.columns]
                
                if available_extras or ('Lưu lượng tổng' in filtered_df.columns):
                    st.markdown("---")
                    cols = st.columns(4) 
                    idx = 0
                    
                    if 'Lưu lượng tổng' in filtered_df.columns:
                        v = filtered_df['Lưu lượng tổng'].dropna()
                        if not v.empty and v.max() > 0:
                            usage = v.max() - v.min()
                            cols[idx % 4].metric("Nước đã dùng", f"{usage:.1f} m³")
                            idx += 1
                    
                    for col in available_extras:
                        val = filtered_df[col].mean()
                        if pd.notnull(val):
                            cols[idx % 4].metric(extra_metrics[col], f"{val:.2f}")
                            idx += 1
        
                # --- 6. BIỂU ĐỒ DIỄN BIẾN (Logic cũ nguyên bản) ---
                st.subheader(f"📈 Biểu đồ diễn biến ({display_type})")
        
                if view_mode in ["Tháng", "Quý", "6 Tháng", "Năm"] and not filtered_df.empty:
                    actual_times = pd.to_datetime(filtered_df['Thời gian'])
                    start_dt = actual_times.min().strftime('%d/%m/%Y')
                    end_dt = actual_times.max().strftime('%d/%m/%Y')
                    st.info(f"📅 **Thông tin:** Trong chế độ xem **{view_mode}**, dữ liệu thực tế ghi nhận từ ngày **{start_dt}** đến ngày **{end_dt}**.")
        
                numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
                chart_metrics = [
                    m for m in numeric_cols 
                    if m not in ['Lưu lượng tổng', 'STT'] 
                    and filtered_df[m].notnull().any() 
                    and (filtered_df[m] != 0).any()
                ]
                
                selected_m = st.multiselect(
                    "Bấm vào đây để thêm thông số:", 
                    chart_metrics, 
                    default=[chart_metrics[0]] if chart_metrics else [],
                    key="chart_multiselect"
                )
        
                if selected_m:
                    chart_data = get_chart_data(filtered_df, view_mode, selected_m, display_type)
                    
                    if chart_data is not None and not chart_data.empty:
                        fig = px.line(
                            chart_data, 
                            labels={"value": "Giá trị", "Thời gian": "Mốc đo"},
                            template="plotly_white",
                            render_mode="webgl"
                        )
        
                        fig.update_traces(
                            mode='lines+markers', 
                            marker=dict(size=8),
                            hovertemplate='Thời gian: %{x|%d/%m/%Y %H:%M}<br>Giá trị: %{y:.2f}'
                        )
        
                        fig.update_layout(
                            hovermode='x unified',
                            margin=dict(l=0, r=0, t=30, b=0)
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
                # --- 7. HIỂN THỊ BẢNG DỮ LIỆU CHI TIẾT (Logic cũ nguyên bản) ---
                from bomvan_logic import process_device_columns
                filtered_df = process_device_columns(filtered_df)
                
                with st.expander("🔍 Xem bảng dữ liệu chi tiết"):
                    # Logic sắp xếp cột của bạn
                    time_related_cols = ['Tên khu', 'Ngày', 'Trạng thái', 'Phương thức hoạt động', 'Người điều khiển']
                    all_cols = filtered_df.columns.tolist()
                    lead_cols = [c for c in time_related_cols if c in all_cols]
                    remaining_cols = [c for c in all_cols if c not in lead_cols and c != 'Thời gian']
                    new_column_order = lead_cols + ['Thời gian'] + remaining_cols
                    
                    st.dataframe(filtered_df[new_column_order])
                    
                st.success("✅ Hệ thống đang vận hành và cập nhật dữ liệu liên tục.")
        else:
            st.info("👈 Vui lòng chọn thời gian, khu vực và các thông số, sau đó nhấn **'XÁC NHẬN VÀ TẢI DỮ LIỆU'** ở menu bên trái.")

    except Exception as e:
        st.error(f"⚠️ Đã xảy ra lỗi: {e}")
