# 7. HIỂN THỊ BẢNG DỮ LIỆU CHI TIẾT
import streamlit as st

def show_data_table(filtered_df):
    st.markdown("---")
    st.subheader("📋 Bảng dữ liệu chi tiết")
            with st.expander("🔍 Xem bảng dữ liệu chi tiết"):
                # Danh sách các cột thời gian muốn đưa lên trước
                time_related_cols = ['Ngày', 'Tháng', 'Năm_Col', 'Tuần_HT', 'Quý_HT', 'Sáu_Tháng_HT']
                
                # Lấy danh sách tất cả các cột hiện có trong filtered_df
                all_cols = filtered_df.columns.tolist()
                
                # Lọc ra những cột thời gian thực sự tồn tại (tránh lỗi nếu thiếu cột)
                lead_cols = [c for c in time_related_cols if c in all_cols]
                
                # Các cột còn lại (bao gồm 'Thời gian' và các chỉ số cảm biến)
                remaining_cols = [c for c in all_cols if c not in lead_cols and c != 'Thời gian']
                
                # Sắp xếp lại thứ tự: [Ngày, Tháng...] -> [Thời gian] -> [Các chỉ số khác]
                new_column_order = lead_cols + ['Thời gian'] + remaining_cols
                
                # Hiển thị bảng với thứ tự cột mới
                st.dataframe(filtered_df[new_column_order], use_container_width=True)
                
            # Thông báo trạng thái vận hành
            st.success("✅ Hệ thống đang vận hành và cập nhật dữ liệu liên tục.")

    except Exception as e:
        st.error(f"⚠️ Đã xảy ra lỗi: {e}")
