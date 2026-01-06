# data_store.py
import pandas as pd
import os
import threading
from datetime import datetime

DATA_FILE = "data.xlsx"

_df_cache = None
_file_mtime = None
_lock = threading.Lock()


def clean_dataframe(df):
    """Membersihkan dataframe: handle NaN, format string, reset index"""
    if df.empty:
        return df
    
    # Fill NaN dengan string kosong
    df = df.fillna("")
    
    # Convert semua kolom ke string (kecuali yang numeric penting)
    for col in df.columns:
        # Skip kolom yang seharusnya numeric
        col_lower = col.lower()
        if any(numeric in col_lower for numeric in ['freq', 'bwidth', 'long', 'lat']):
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna("")
            except:
                df[col] = df[col].astype(str)
        else:
            df[col] = df[col].astype(str)
    
    # Reset whitespace - PERBAIKAN: gunakan .map() bukan .applymap()
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    
    # Reset index dan tambahkan kolom no jika tidak ada
    df = df.reset_index(drop=True)
    if "no" not in df.columns and "No" not in df.columns:
        df.insert(0, "no", range(1, len(df) + 1))
    
    return df


def load_data():
    """Load data dari Excel dengan caching"""
    global _df_cache, _file_mtime
    
    print(f"Loading data from {DATA_FILE}...")
    
    if not os.path.exists(DATA_FILE):
        print("Data file not found, returning empty DataFrame")
        return pd.DataFrame()
    
    try:
        mtime = os.path.getmtime(DATA_FILE)
        
        # Jika cache kosong atau file berubah
        if _df_cache is None or _file_mtime != mtime:
            with _lock:
                print(f"Reading Excel file (modified: {datetime.fromtimestamp(mtime)})")
                
                try:
                    # Coba baca dengan openpyxl
                    df = pd.read_excel(DATA_FILE, dtype=str, engine="openpyxl")
                    print(f"Successfully read Excel with openpyxl. Shape: {df.shape}")
                except Exception as e1:
                    print(f"Error with openpyxl: {e1}. Trying with default engine...")
                    try:
                        df = pd.read_excel(DATA_FILE, dtype=str)
                        print(f"Successfully read Excel with default engine. Shape: {df.shape}")
                    except Exception as e2:
                        print(f"Error reading Excel: {e2}")
                        return pd.DataFrame()
                
                # Bersihkan data
                df = clean_dataframe(df)
                
                # Simpan ke cache
                _df_cache = df
                _file_mtime = mtime
                
                print(f"Cache updated. Columns: {df.columns.tolist()}")
                if len(df) > 0:
                    print(f"First few rows: {df.head(3).to_dict('records')}")
        
        return _df_cache.copy() if _df_cache is not None else pd.DataFrame()
        
    except Exception as e:
        print(f"Critical error in load_data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def save_data(df):
    """Simpan dataframe ke Excel"""
    global _df_cache, _file_mtime
    with _lock:
        try:
            # Bersihkan data sebelum simpan
            df = clean_dataframe(df)
            
            # Simpan ke file
            df.to_excel(DATA_FILE, index=False, engine="openpyxl")
            
            # Update cache
            _df_cache = df.copy()
            _file_mtime = os.path.getmtime(DATA_FILE)
            
            print(f"Data saved successfully. Shape: {df.shape}")
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False


def clear_cache():
    """Clear cache untuk memaksa reload"""
    global _df_cache, _file_mtime
    _df_cache = None
    _file_mtime = None
    print("Cache cleared")


def get_data_info():
    """Debug function untuk melihat info data"""
    df = load_data()
    info = {
        "file_exists": os.path.exists(DATA_FILE),
        "file_size": os.path.getsize(DATA_FILE) if os.path.exists(DATA_FILE) else 0,
        "rows": len(df),
        "columns": df.columns.tolist(),
        "sample": df.head(3).to_dict('records') if not df.empty else []
    }
    return info