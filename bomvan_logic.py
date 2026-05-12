import pandas as pd

def parse_device_status(status_str, prefix="Bơm"):
    """
    Giải mã chuỗi từ file JSON: '1-0/6-0/3-1'
    """
    # Kiểm tra nếu dữ liệu trống hoặc không hợp lệ
    if pd.isna(status_str) or str(status_str).strip() in ["0", "", "nan"]:
        return "Tất cả tắt"
    
    try:
        # Tách các cụm thiết bị (ví dụ: '1-0', '6-0', '3-1')
        parts = str(status_str).split('/')
        active_devices = []
        
        for p in parts:
            p = p.strip() # Xóa khoảng trắng thừa nếu có
            if '-' in p:
                # Tách ID và Trạng thái (ví dụ: '3' và '1')
                device_info = p.split('-')
                if len(device_info) == 2:
                    device_id = device_info[0].strip()
                    state = device_info[1].strip()
                    
                    # So sánh: chỉ cần là '1' thì coi như Bật
                    if state == "1":
                        active_devices.append(f"{prefix} {device_id}")
        
        if not active_devices:
            return "Tất cả tắt"
        
        # Sắp xếp số hiệu bơm cho đẹp (ví dụ: Bơm 1, Bơm 3)
        return ", ".join(active_devices)
    except Exception as e:
        return f"Lỗi: {str(e)}"

def process_device_columns(df):
    """
    Hàm bổ sung cột hiển thị vào DataFrame
    """
    new_df = df.copy()
    
    # Xử lý cho cột Bơm
    if 'Bơm' in new_df.columns:
        new_df['Bơm bật'] = new_df['Bơm'].apply(lambda x: parse_device_status(x, "Bơm"))
    
    # Xử lý cho cột Van
    if 'Van' in new_df.columns:
        new_df['Van bật'] = new_df['Van'].apply(lambda x: parse_device_status(x, "Van"))
        
    return new_df
