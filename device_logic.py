import pandas as pd

def parse_device_status(status_str, prefix="Bơm"):
    """
    Giải mã chuỗi '1-0/6-0/3-1' thành 'Bơm 3 Bật'
    """
    if pd.isna(status_str) or status_str == "0" or status_str == "":
        return "Tất cả tắt"
    
    try:
        # Tách chuỗi theo dấu '/'
        parts = str(status_str).split('/')
        active_devices = []
        
        for p in parts:
            if '-' in p:
                device_id, state = p.split('-')
                if state.strip() == "1":
                    active_devices.append(f"{prefix} {device_id}")
        
        if not active_devices:
            return "Tất cả tắt"
        
        # Trả về danh sách các thiết bị đang bật, cách nhau bởi dấu phẩy
        return ", ".join(active_devices)
    except:
        return "Lỗi định dạng"

def process_device_columns(df):
    """
    Hàm bổ sung thêm 2 cột hiển thị trạng thái thiết bị vào DataFrame
    """
    new_df = df.copy()
    
    if 'Bơm' in new_df.columns:
        new_df['Trạng thái Bơm'] = new_df['Bơm'].apply(lambda x: parse_device_status(x, "Bơm"))
        
    if 'Van' in new_df.columns:
        new_df['Trạng thái Van'] = new_df['Van'].apply(lambda x: parse_device_status(x, "Van"))
        
    return new_df
