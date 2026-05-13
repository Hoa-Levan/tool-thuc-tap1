import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import timedelta
from hourly_logic import handle_hourly_view
from display_logic import get_chart_data
from zone_logic import handle_zone_selection
from bomvan_logic import process_device_columns

# Cấu hình trang và Giao diện
st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp Toàn diện", layout="wide")
st.title("🍀 Công cụ Phân tích Dữ liệu Nông nghiệp")

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
    def cleanup_monitoring_columns(df):
        new_df = df.copy()
        
        # 1. Xử lý NHIỆT ĐỘ
        # Ưu tiên lấy dữ liệu từ 'tempKK' nếu 'Nhiệt độ' bị trống hoặc bằng 0
        if 'tempKK' in new_df.columns and 'Nhiệt độ' in new_df.columns:
            new_df['Nhiệt độ'] = new_df.apply(
                lambda row: row['tempKK'] if (pd.isna(row['Nhiệt độ']) or row['Nhiệt độ'] == 0) else row['Nhiệt độ'], 
                axis=1
            )
        elif 'tempKK' in new_df.columns:
            new_df = new_df.rename(columns={'tempKK': 'Nhiệt độ'})
    
        # 2. Xử lý ĐỘ ẨM
        if 'humiKK' in new_df.columns and 'Độ ẩm' in new_df.columns:
            new_df['Độ ẩm'] = new_df.apply(
                lambda row: row['humiKK'] if (pd.isna(row['Độ ẩm']) or row['Độ ẩm'] == 0) else row['Độ ẩm'], 
                axis=1
            )
        elif 'humiKK' in new_df.columns:
            new_df = new_df.rename(columns={'humiKK': 'Độ ẩm'})
    
        # 3. Xóa các cột thừa và các cột nhiệt độ trùng lặp khác
        # Bạn liệt kê tất cả các tên cột muốn xóa vào đây
        cols_to_drop = ['tempKK', 'humiKK', 'Nhiệt độ EC', 'Nhiệt độ PH'] 
        # Lưu ý: 'Nhiệt độ EC/PH' thường là nhiệt độ dung dịch, nếu không cần thì xóa cho gọn
        
        existing_drop_cols = [c for c in cols_to_drop if c in new_df.columns]
        new_df = new_df.drop(columns=existing_drop_cols)
        
        return new_df
    
    # GỌI HÀM SAU KHI LOAD DF
    df = cleanup_monitoring_columns(df)
        
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
            
            # --- NHÓM 1: CHỌN THỜI GIAN (Gần nhau để thẩm mỹ) ---
            view_mode = st.selectbox(
                "Chọn chế độ xem:", 
                ["Ngày", "Xem theo Giờ", "Tuần", "Tháng", "Quý", "6 Tháng", "Năm"]
            )
            
            filtered_df = pd.DataFrame()
            sel_label = ""

            # Logic hiển thị bộ chọn dựa trên view_mode
            if view_mode == "Xem theo Giờ":
                # Gọi logic từ file hourly_logic.py
                filtered_df, sel_label = handle_hourly_view(df)
                
            elif view_mode == "Ngày":
                targets = sorted(df['Ngày'].unique(), reverse=True)
                sel_label = st.selectbox("Chọn ngày:", targets)
                filtered_df = df[df['Ngày'] == sel_label].copy()
                
            elif view_mode == "Tuần":
                order = df.groupby('Tuần_HT')['Thời gian'].min().sort_values(ascending=False).index
                sel_label = st.selectbox("Chọn tuần:", order)
                filtered_df = df[df['Tuần_HT'] == sel_label].copy()
                
            elif view_mode == "Tháng":
                order = df.groupby('Tháng')['Thời gian'].min().sort_values(ascending=False).index
                sel_label = st.selectbox("Chọn tháng:", order)
                filtered_df = df[df['Tháng'] == sel_label].copy()
                
            elif view_mode == "Quý":
                order = df.groupby('Quý_HT')['Thời gian'].min().sort_values(ascending=False).index
                sel_label = st.selectbox("Chọn quý:", order)
                filtered_df = df[df['Quý_HT'] == sel_label].copy()
                
            elif view_mode == "6 Tháng":
                order = df.groupby('Sáu_Tháng_HT')['Thời gian'].min().sort_values(ascending=False).index
                sel_label = st.selectbox("Chọn giai đoạn 6 tháng:", order)
                filtered_df = df[df['Sáu_Tháng_HT'] == sel_label].copy()
                
            elif view_mode == "Năm":
                targets = sorted(df['Năm_Col'].unique(), reverse=True)
                sel_label = st.selectbox("Chọn năm:", targets)
                filtered_df = df[df['Năm_Col'] == sel_label].copy()

            # --- KHOẢNG CÁCH NGĂN CÁCH ---
            st.markdown("---")
            
            # --- NHÓM 2: TÙY CHỈNH BIỂU ĐỒ (Ở một góc riêng phía dưới) ---
            st.markdown("### 🎨 Tùy chỉnh biểu đồ")
            display_type = st.radio(
                "Kiểu hiển thị số liệu:",
                ["Số liệu trung bình cộng", "Số liệu thô"],
                help="Chọn 'Mỗi lần đo' để xem chi tiết dữ liệu gốc (ô rỗng sẽ hiện là 0)."
            )
            # Tìm đoạn code gọi handle_zone_selection và sửa thành:
            filtered_df, current_zone, column_order = handle_zone_selection(df, filtered_df)

        # 5. HIỂN THỊ SỐ LIỆU TRUNG BÌNH
        if not filtered_df.empty:
            display_label = sel_label if current_zone == "Tất cả" else f"Tất cả lịch sử khu {current_zone}"
            st.subheader(f"📊 Số liệu trung bình: {display_label}")
            
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
                'N': 'Nitơ (N)',
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

            # --- 6. BIỂU ĐỒ DIỄN BIẾN ---
        st.subheader(f"📈 Biểu đồ diễn biến ({display_type})")

        # Logic hiển thị thông báo khoảng thời gian thực tế
        if view_mode in ["Tháng", "Quý", "6 Tháng", "Năm"] and not filtered_df.empty:
            actual_times = pd.to_datetime(filtered_df['Thời gian'])
            start_dt = actual_times.min().strftime('%d/%m/%Y')
            end_dt = actual_times.max().strftime('%d/%m/%Y')
            st.info(f"📅 **Thông tin:** Trong chế độ xem **{view_mode}**, dữ liệu thực tế ghi nhận từ ngày **{start_dt}** đến ngày **{end_dt}**.")

        # Lọc danh sách cột số hợp lệ để vẽ biểu đồ
        numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
        chart_metrics = [
            m for m in numeric_cols 
            if m not in ['Lưu lượng tổng', 'STT'] 
            and filtered_df[m].notnull().any() 
            and (filtered_df[m] != 0).any()
        ]
        
        # Chọn thông số hiển thị
        selected_m = st.multiselect(
            "Bấm vào đây để thêm thông số:", 
            chart_metrics, 
            default=[chart_metrics[0]] if chart_metrics else []
        )

        if selected_m:
            # Lấy dữ liệu đã qua xử lý để vẽ biểu đồ
            chart_data = get_chart_data(filtered_df, view_mode, selected_m, display_type)
            
            # Thông báo hỗ trợ nếu xem theo Tuần nhưng chỉ có 1 ngày dữ liệu
            if view_mode == "Tuần" and not filtered_df.empty:
                if filtered_df['Ngày'].nunique() == 1:
                    st.info(f"💡 Dữ liệu tuần này chỉ có của ngày {filtered_df['Ngày'].iloc[0]}.")

            # Kiểm tra và tiến hành vẽ biểu đồ
            if chart_data is not None and not chart_data.empty:
                # Tạo đối tượng biểu đồ với render_mode="webgl" để chống lag
                fig = px.line(
                    chart_data, 
                    labels={"value": "Giá trị", "Thời gian": "Mốc đo"},
                    template="plotly_white",
                    render_mode="webgl"
                )

                # Cấu hình hiển thị: 
                # - 'lines+markers': giúp thấy rõ các điểm Bật/Tắt ngay cả khi trùng giá trị
                # - hovertemplate: định dạng ngày giờ và số thập phân khi rê chuột
                fig.update_traces(
                    mode='lines+markers', 
                    marker=dict(size=8),
                    hovertemplate='Thời gian: %{x|%d/%m/%Y %H:%M}<br>Giá trị: %{y:.2f}'
                )

                # Tối ưu hóa layout: tăng tốc độ phản hồi khi di chuyển chuột
                fig.update_layout(
                    hovermode='x unified',
                    margin=dict(l=0, r=0, t=30, b=0)
                )
        
                # Hiển thị biểu đồ lên Streamlit
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Không có dữ liệu phù hợp để hiển thị biểu đồ.")

            # 7. HIỂN THỊ BẢNG DỮ LIỆU CHI TIẾT
            from bomvan_logic import process_device_columns
            filtered_df = process_device_columns(filtered_df)
            
            with st.expander("🔍 Xem bảng dữ liệu chi tiết"):
                # Danh sách các cột thời gian muốn đưa lên trước
                time_related_cols = ['Tên khu', 'Ngày', 'Trạng thái', 'Phương thức hoạt động', 'Người điều khiển']
                
                # Lấy danh sách tất cả các cột hiện có trong filtered_df
                all_cols = filtered_df.columns.tolist()
                
                # Lọc ra những cột thời gian thực sự tồn tại (tránh lỗi nếu thiếu cột)
                lead_cols = [c for c in time_related_cols if c in all_cols]
                
                # Các cột còn lại (bao gồm 'Thời gian' và các chỉ số cảm biến)
                remaining_cols = [c for c in all_cols if c not in lead_cols and c != 'Thời gian']
                
                # Sắp xếp lại thứ tự: [Ngày, Tháng...] -> [Thời gian] -> [Các chỉ số khác]
                new_column_order = lead_cols + ['Thời gian'] + remaining_cols
                
                # Hiển thị bảng với thứ tự cột mới
                st.dataframe(filtered_df[new_column_order])
                
            # Thông báo trạng thái vận hành
            st.success("✅ Hệ thống đang vận hành và cập nhật dữ liệu liên tục.")

    except Exception as e:
        st.error(f"⚠️ Đã xảy ra lỗi: {e}")
