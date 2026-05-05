import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Hệ thống Phân tích Đa năng", layout="wide")
st.title("🍀 Công cụ Phân tích Dữ liệu Nông nghiệp")

uploaded_file = st.file_uploader("Nạp tệp tin JSON (Quang trắc hoặc Nhỏ giọt)", type=['json'])

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)
        
        # 1. XỬ LÝ THỜI GIAN
        df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
        df = df.dropna(subset=['Thời gian'])
        df['Ngày'] = df['Thời gian'].dt.date
        df = df.sort_values('Thời gian')

        # 2. CHUẨN HÓA CỘT DỮ LIỆU (Ép kiểu số cho tất cả cột quan trọng)
        all_potential_cols = [
            'soil_ASKK', 'tempKK', 'humiKK', 'AS', 'Lưu lượng m2/h', 
            'Lưu lượng tổng', 'EC', 'PH', 'Nhiệt Độ', 'Độ ẩm', 'TBEC', 'TBPH'
        ]
        for col in all_potential_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Xử lý lỗi Nhiệt độ bị nhân 10 (331 -> 33.1)
        for t_col in ['Nhiệt Độ', 'tempKK']:
            if t_col in df.columns:
                df[t_col] = df[t_col].apply(lambda x: x/10 if x > 100 else x)

        # 3. BỘ LỌC NGÀY
        st.sidebar.header("Bộ lọc")
        list_days = sorted(df['Ngày'].unique(), reverse=True)
        selected_date = st.sidebar.selectbox("Chọn ngày:", list_days)
        filtered_df = df[df['Ngày'] == selected_date]

        # 4. ĐÁNH GIÁ CHUYÊN SÂU (Hiển thị linh hoạt theo file)
        st.subheader(f"📝 Đánh giá chuyên sâu ngày {selected_date}")
        
        # Tạo các cột hiển thị tùy biến
        cols = st.columns(4)
        
        # Ô 1: Ánh sáng (Dành cho file Quang trắc)
        if 'soil_ASKK' in filtered_df.columns:
            with cols[0]:
                val = filtered_df['soil_ASKK'].mean()
                if not pd.isna(val):
                    st.metric("Ánh sáng (Lux)", f"{val:.1f}")
                    st.caption("☀️ >10000: Mạnh | <5000: Yếu")

        # Ô 2: Nhiệt độ & Độ ẩm (Dò tìm cột tương ứng)
        with cols[1]:
            t_val = filtered_df['tempKK'].mean() if 'tempKK' in filtered_df.columns else filtered_df['Nhiệt Độ'].mean()
            h_val = filtered_df['humiKK'].mean() if 'humiKK' in filtered_df.columns else filtered_df['Độ ẩm'].mean()
            if not pd.isna(t_val): st.metric("Nhiệt độ trung bình", f"{t_val:.1f} °C")
            if not pd.isna(h_val): st.metric("Độ ẩm trung bình", f"{h_val:.1f} %")

        # Ô 3: EC & PH (Dành cho file Nhỏ giọt)
        with cols[2]:
            ec_val = filtered_df['TBEC'].mean() if 'TBEC' in filtered_df.columns else filtered_df['EC'].mean()
            ph_val = filtered_df['TBPH'].mean() if 'TBPH' in filtered_df.columns else filtered_df['PH'].mean()
            if not pd.isna(ec_val): st.metric("Chỉ số EC", f"{ec_val:.1f}")
            if not pd.isna(ph_val): 
                # Nếu pH đang ở dạng 450 -> 4.5
                if ph_val > 14: ph_val = ph_val / 100
                st.metric("Chỉ số pH", f"{ph_val:.2f}")

        # Ô 4: Áp suất & Lưu lượng
        with cols[3]:
            if 'AS' in filtered_df.columns:
                as_val = filtered_df['AS'].mean()
                if not pd.isna(as_val): st.metric("Áp suất (AS)", f"{as_val:.2f}")
            if 'Lưu lượng m2/h' in filtered_df.columns:
                f_val = filtered_df['Lưu lượng m2/h'].mean()
                st.metric("Lưu lượng m2/h", f"{f_val:.2f}")

        # 5. BIỂU ĐỒ (Sửa lỗi trống trơn)
        st.subheader("📈 Biểu đồ diễn biến")
        
        # Chỉ lấy những cột thực sự có số liệu để người dùng chọn
        available_metrics = [c for c in all_potential_cols if c in filtered_df.columns and not filtered_df[c].isnull().all()]
        
        if available_metrics:
            selected = st.multiselect("Chọn thông số muốn vẽ biểu đồ:", available_metrics, default=[available_metrics[0]])
            
            if selected:
                # CƯỚNG ÉP VẼ BIỂU ĐỒ: Xử lý dữ liệu để chắc chắn không trống
                chart_data = filtered_df[['Thời gian'] + selected].copy()
                chart_data = chart_data.set_index('Thời gian')
                
                # Sử dụng biểu đồ đường của Streamlit
                st.line_chart(chart_data)
        else:
            st.warning("Không tìm thấy dữ liệu số để vẽ biểu đồ.")

        with st.expander("Xem bảng dữ liệu chi tiết"):
            st.write(filtered_df)

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý tệp: {e}")
