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
        exclude_cols = ['Thời gian', 'Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT', 'STT']
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
            
            # Hàng 1: Các chỉ số môi trường & Nước
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                t_col = next((c for c in ['Nhiệt Độ', 'tempKK', 'nhiệt độ EC'] if c in filtered_df.columns), None)
                if t_col:
                    t_val = filtered_df[t_col].mean()
                    if t_val > 150: t_val /= 10
                    st.metric("Nhiệt độ TB", f"{t_val:.1f} °C")
            with c2:
                # Ưu tiên hiện Nước, nếu không có hiện PH
                usage = 0.0
                has_water = False
                if 'Lưu lượng tổng' in filtered_df.columns:
                    v = filtered_df['Lưu lượng tổng'].dropna()
                    if not v.empty and v.max() > 0:
                        usage = v.max() - v.min()
                        has_water = True
                
                if has_water:
                    st.metric("Nước đã dùng", f"{usage:.1f} m³")
                else:
                    ph_col = next((c for c in ['PH', 'TBPH'] if c in filtered_df.columns), None)
                    if ph_col: st.metric("PH trung bình", f"{filtered_df[ph_col].mean():.2f}")
            with c3:
                # TÁCH RIÊNG ĐỘ ẨM KHÔNG KHÍ
                if 'humiKK' in filtered_df.columns:
                    st.metric("Độ ẩm KK", f"{filtered_df['humiKK'].mean():.1f} %")
            with c4:
                # TÁCH RIÊNG ĐỘ ẨM ĐẤT
                if 'Độ ẩm' in filtered_df.columns:
                    st.metric("Độ ẩm Đất", f"{filtered_df['Độ ẩm'].mean():.1f} %")

            # Hàng 2: Dinh dưỡng (N, P, K, EC)
            st.markdown("---")
            n_col, p_col, k_col, ec_col = st.columns(4)
            with n_col:
                if 'N' in filtered_df.columns: st.metric("Nitơ (N)", f"{filtered_df['N'].mean():.1f}")
            with p_col:
                if 'P' in filtered_df.columns: st.metric("Photpho (P)", f"{filtered_df['P'].mean():.1f}")
            with k_col:
                if 'K' in filtered_df.columns: st.metric("Kali (K)", f"{filtered_df['K'].mean():.1f}")
            with ec_col:
                e_col = next((c for c in ['TBEC', 'EC'] if c in filtered_df.columns), None)
                if e_col: st.metric("EC trung bình", f"{filtered_df[e_col].mean():.1f}")

            # Hàng 2: Chỉ số dinh dưỡng (N, P, K) - Chỉ hiện nếu có dữ liệu
            nutrients = [c for c in ['N', 'P', 'K'] if c in filtered_df.columns]
            if nutrients:
                st.markdown("---")
                n_col, p_col, k_col, empty_col = st.columns(4)
                with n_col:
                    if 'N' in filtered_df.columns: st.metric("Nitơ (N)", f"{filtered_df['N'].mean():.1f}")
                with p_col:
                    if 'P' in filtered_df.columns: st.metric("Photpho (P)", f"{filtered_df['P'].mean():.1f}")
                with k_col:
                    if 'K' in filtered_df.columns: st.metric("Kali (K)", f"{filtered_df['K'].mean():.1f}")

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
