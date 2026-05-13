import streamlit as st

def init_control_state():
    if 'is_confirmed' not in st.session_state:
        st.session_state.is_confirmed = False

def render_confirm_button():
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 Bảng điều khiển")
    
    # Khi nhấn nút này, is_confirmed sẽ lên True
    if st.sidebar.button("🔥 XÁC NHẬN VÀ TẢI DỮ LIỆU", use_container_width=True, type="primary"):
        st.session_state.is_confirmed = True
        # Không dùng st.rerun() ở đây nữa để tránh vòng lặp

def should_load():
    # Lấy giá trị hiện tại
    val = st.session_state.get('is_confirmed', False)
    # QUAN TRỌNG: Sau khi kiểm tra, ta trả về True để chạy nốt lần này, 
    # nhưng bí mật reset nó về False cho lần thay đổi widget tiếp theo.
    if val:
        st.session_state.is_confirmed = False
        return True
    return False
