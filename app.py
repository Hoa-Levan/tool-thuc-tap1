import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp", layout="wide")
st.title("🍀 Công cụ Phân tích Dữ liệu Nông nghiệp")

uploaded_file = st.file_uploader("Nạp tệp tin JSON", type=['json'])

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)
        
        # 1. XỬ LÝ THỜI GIAN
        df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
        df = df.dropna(subset=['Thời gian']).sort_values('Thời gian')
        df['Ngày'] = df['Thời gian'].dt.date

        # 2. CHUẨN HÓA CỘT DỮ LIỆU (Ép kiểu số an toàn)
        # Bao gồm tất cả các tên cột có thể xuất hiện trong các file của bạn
        potential_cols = [
            'soil_ASKK', 'tempKK', 'humiKK', 'AS', 'Lưu lượng m2/h', 
            'Lưu lượng tổng', 'EC', 'PH', 'Nhiệt Độ', 'Độ ẩm', 'TBEC', 'TBPH'
        ]
        
        for col in potential_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Sửa lỗi nhiệt độ bị nhân 10 (ví dụ 331 -> 33.1) - Xử lý an toàn với giá trị NaN
        def fix_temp(x):
            if pd.isna(x): return x
            return x / 10 if x > 100 else x

        for t_col in ['Nhiệt Độ', 'tempKK']:
            if t_col in df.columns:
                df[t_col] = df[t_col].apply(fix_temp)

        # 3. BỘ LỌC NGÀY
        st.sidebar.header("Bộ lọc")
        list_days = sorted(df['Ngày'].unique(), reverse=True)
        selected_date = st.sidebar.selectbox("Chọn ngày:", list_days)
        filtered_df = df[df['Ngày'] == selected_date].copy()

        # 4. ĐÁNH GIÁ CHUYÊN SÂU
        st.subheader(f"📝 Đánh giá chuyên sâu ngày {selected_date}")
        cols = st.columns(4)
        
        # Ô 1: Ánh sáng (soil_ASKK)
        with cols[0]:
            if 'soil_ASKK' in filtered_df.columns:
                val = filtered_df['soil_ASKK'].mean()
                if not pd.isna(val) and val > 0:
                    st.metric("Ánh sáng (Lux)", f"{val:.1f}")
                    if val > 10000: st.warning("☀️ Ánh sáng mạnh")
                    else: st.success("✅ Ánh sáng đủ")

        # Ô 2: Nhiệt độ & Độ ẩm
        with cols[1]:
            t_val = filtered_df['tempKK'].mean() if 'tempKK' in filtered_df.columns else filtered_df['Nhiệt Độ'].mean()
            h_val = filtered_df['humiKK'].mean() if 'humiKK' in filtered_df.columns else filtered_df['Độ ẩm'].mean()
            if not pd.isna(t_val): st.metric("Nhiệt độ", f"{t_val:.1f} °C")
            if not pd.isna(h_val): st.metric("Độ ẩm", f"{h_val:.1f} %")

        # Ô 3: EC & PH (Dò tìm TBEC/TBPH hoặc EC/PH)
        with cols[2]:
            ec_val = filtered_df['TBEC'].mean() if 'TBEC' in filtered_df.columns and filtered_df['TBEC'].mean() > 0 else filtered_df['EC'].mean()
            ph_val = filtered_df['TBPH'].mean() if 'TBPH' in filtered_df.columns and filtered_df['TBPH'].mean() > 0 else filtered_df['PH'].mean()
            
            if not pd.isna(ec_val) and ec_val > 0: st.metric("Chỉ số EC", f"{ec_val:.1f}")
            if not pd.isna(ph_val) and ph_val > 0:
                if ph_val > 14: ph_val = ph_val / 100 # Chuyển 450 thành 4.5
                st.metric("Chỉ số pH", f"{ph_val:.2f}")

        # Ô 4: Áp suất & Lưu lượng
        with cols[3]:
            if 'AS' in filtered_df.columns:
                as_val = filtered_df['AS'].mean()
                if not pd.isna(as_val): st.metric("Áp suất (AS)", f"{as_val:.2f}")
            if 'Lưu lượng tổng' in filtered_df.columns:
                total_flow = filtered_df['Lưu lượng tổng'].iloc[-1] # Lấy giá trị cuối cùng của ngày
                st.metric("Lưu lượng tổng", f"{total_flow:.1f}")

        # 5. BIỂU ĐỒ DIỄN BIẾN
        st.subheader("📈 Biểu đồ diễn biến")
        
        # Lọc danh sách cột có dữ liệu thực tế để vẽ
        available_metrics = [c for c in potential_cols if c in filtered_df.columns and not filtered_df[c].dropna().empty]
        
        if available_metrics:
            selected = st.multiselect("Chọn thông số muốn xem:", available_metrics, default=[available_metrics[0]])
            if selected:
                # Vẽ biểu đồ đường
                st.line_chart(filtered_df.set_index('Thời gian')[selected])
        else:
            st.info("Không có dữ liệu số để hiển thị biểu đồ.")

        with st.expander("Bảng dữ liệu chi tiết"):
            st.dataframe(filtered_df)

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
