import streamlit as st

def init_control_state():
    """Khởi tạo trạng thái xác nhận nếu chưa có"""
    if 'is_confirmed' not in st.session_state:
        st.session_state.is_confirmed = False

def render_confirm_button():
    """Hiển thị nút bấm xác nhận tổng ở Sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 Bảng điều khiển")
    
    # Nút xác nhận
    if st.sidebar.button("🔥 XÁC NHẬN VÀ TẢI DỮ LIỆU", use_container_width=True, type="primary"):
        st.session_state.is_confirmed = True
        st.rerun() # Buộc app chạy lại để áp dụng dữ liệu mới

    # Nút reset nếu muốn chọn lại từ đầu
    if st.sidebar.button("🔄 Thiết lập lại lựa chọn"):
        st.session_state.is_confirmed = False
        st.rerun()

def should_load():
    """Kiểm tra xem đã được phép load dữ liệu chưa"""
    return st.session_state.get('is_confirmed', False)
