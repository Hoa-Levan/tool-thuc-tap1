import pandas as pd

def get_chart_data(filtered_df, view_mode, selected_m, display_type):
    df_plot = filtered_df.copy()
    df_plot['Thời gian'] = pd.to_datetime(df_plot['Thời gian'])
    df_plot = df_plot.set_index('Thời gian').sort_index()
    
    is_single_day = filtered_df['Ngày'].nunique() == 1

    # --- TRƯỜNG HỢP: SỐ LIỆU THÔ (GIỮ NGUYÊN CẤU TRÚC TỪNG CHẾ ĐỘ XEM) ---
    if display_type == "Số liệu thô":
        if view_mode == "Ngày":
            return df_plot[selected_m].fillna(0)
            
        elif view_mode == "Xem theo Giờ":
            return df_plot[selected_m].fillna(0)
            
        elif view_mode == "Tuần":
            if is_single_day: return df_plot[selected_m].fillna(0)
            return df_plot[selected_m].resample('30min').first().fillna(0)
            
        elif view_mode == "Tháng":
            if is_single_day: return df_plot[selected_m].fillna(0)
            return df_plot[selected_m].resample('30min').first().fillna(0)
            
        elif view_mode == "Quý":
            # Giữ 1 giờ 1 lần như bạn yêu cầu vì không lag
            return df_plot[selected_m].resample('1h').first().fillna(0)
            
        elif view_mode == "6 Tháng":
            # Tăng lên 2 giờ 1 lần để giảm lag
            return df_plot[selected_m].resample('2h').first().fillna(0)
            
        elif view_mode == "Năm":
            # Tăng lên 2 giờ 1 lần để giảm lag
            return df_plot[selected_m].resample('2h').first().fillna(0)

    # --- TRƯỜNG HỢP: TRUNG BÌNH CỘNG ---
    else:
        if view_mode == "Ngày":
            return df_plot[selected_m].resample('h').mean().fillna(0)
            
        elif view_mode == "Xem theo Giờ":
            return df_plot[selected_m].resample('5min').mean().fillna(0)
            
        # Các chế độ còn lại tính trung bình theo Ngày để biểu đồ mượt hơn
        else:
            if is_single_day:
                return df_plot[selected_m].resample('h').mean().fillna(0)
            return filtered_df.groupby('Ngày')[selected_m].mean().sort_index().fillna(0)
    
