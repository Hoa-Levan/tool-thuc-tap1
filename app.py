import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Hệ thống Phân tích Nông nghiệp", layout="wide")
st.title("📊 Công cụ Phân tích & Lọc dữ liệu Đa năng")

uploaded_file = st.file_uploader("Nạp tệp tin JSON của bạn", type=['json'])

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)
        
        # CHUẨN HÓA DỮ LIỆU
        df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
        df = df.dropna(subset=['Thời gian']) # Loại bỏ dòng không có thời gian
        df['Ngày'] = df['Thời gian'].dt.date
        
        # Chuyển đổi tất cả các cột số tiềm năng
        numeric_cols = ['soil_ASKK', 'tempKK', 'humiKK', 'Lưu lượng m2/h', 'Nhiệt Độ', 'Độ ẩm', 'EC', 'PH', 'AS']
        for col in numeric_cols:
            if col in df.columns:
                # Ép kiểu số và xử lý các ô trống
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # BỘ LỌC
        st.sidebar.header("Bộ lọc")
        list_days = sorted(df['Ngày'].unique(), reverse=True)
        selected_date = st.sidebar.selectbox("Chọn ngày:", list_days)

        if selected_date:
            filtered_df = df[df['Ngày'] == selected_date].sort_values('Thời gian')
            
            # 1. KHU VỰC ĐÁNH GIÁ (Thêm các thông số khác)
            st.subheader(f"📝 Đánh giá thông số ngày {selected_date}")
            m1, m2, m3, m4 = st.columns(4)
            
            with m1:
                if 'soil_ASKK' in filtered_df.columns:
                    val = filtered_df['soil_ASKK'].mean()
                    st.metric("Ánh sáng trung bình", f"{val:.1f}")
                    st.caption("☀️ >15k: Mạnh | ☁️ <5k: Yếu")
            
            with m2:
                t_val = filtered_df['tempKK'].mean() if 'tempKK' in filtered_df.columns else filtered_df['Nhiệt Độ'].mean()
                if not pd.isna(t_val):
                    # Sửa lỗi nhiệt độ bị nhân 10 trong một số file
                    if t_val > 100: t_val = t_val / 10
                    st.metric("Nhiệt độ trung bình", f"{t_val:.1f} °C")
                    if t_val > 30: st.warning("🌡️ Khá nóng")
                    else: st.success("🌡️ Mát mẻ")

            with m3:
                h_val = filtered_df['humiKK'].mean() if 'humiKK' in filtered_df.columns else filtered_df['Độ ẩm'].mean()
                if not pd.isna(h_val):
                    st.metric("Độ ẩm trung bình", f"{h_val:.1f} %")
                    if h_val < 50: st.warning("🌵 Độ ẩm thấp")
                    else: st.info("💧 Độ ẩm tốt")

            with m4:
                if 'Lưu lượng m2/h' in filtered_df.columns:
                    f_val = filtered_df['Lưu lượng m2/h'].mean()
                    st.metric("Lưu lượng tưới", f"{f_val:.2f} m2/h")
                    st.success("💧 Đang vận hành")

            # 2. KHU VỰC BIỂU ĐỒ (Chọn linh hoạt)
            st.subheader("📈 Biểu đồ diễn biến")
            
            # Lấy danh sách các cột thực sự có dữ liệu số để người dùng chọn
            available_cols = [c for c in numeric_cols if c in filtered_df.columns and not filtered_df[c].isnull().all()]
            
            if available_cols:
                selected_metrics = st.multiselect(
                    "Chọn thông số muốn xem trên biểu đồ:",
                    options=available_cols,
                    default=[available_cols[0]]
                )
                
                if selected_metrics:
                    # Tạo dataframe riêng cho biểu đồ để tránh lỗi trục tọa độ
                    chart_data = filtered_df.set_index('Thời gian')[selected_metrics]
                    st.line_chart(chart_data)
                else:
                    st.info("Hãy chọn ít nhất một thông số để xem biểu đồ.")
            else:
                st.error("Không tìm thấy dữ liệu số hợp lệ trong ngày này để vẽ biểu đồ.")

            with st.expander("Dữ liệu chi tiết"):
                st.dataframe(filtered_df)
                
    except Exception as e:
        st.error(f"Lỗi xử lý file: {e}")
