# fix_permissions.py
import os
import pandas as pd

def check_and_fix():
    BASE_DIR = "/home/agnessabrina1/dasims"
    
    # Folder yang perlu dicek
    folders = [
        BASE_DIR,
        os.path.join(BASE_DIR, "uploads"),
        os.path.join(BASE_DIR, "static"),
        os.path.join(BASE_DIR, "templates")
    ]
    
    # File yang perlu dicek
    files = [
        os.path.join(BASE_DIR, "data.xlsx"),
        os.path.join(BASE_DIR, "data_pemeriksaan_tersimpan.xlsx")
    ]
    
    print("=== Checking Permissions ===")
    
    # Cek folder
    for folder in folders:
        if not os.path.exists(folder):
            print(f"Creating folder: {folder}")
            os.makedirs(folder, exist_ok=True)
        
        # Set permission
        try:
            os.chmod(folder, 0o755)
            print(f"✓ Folder: {folder} - OK")
        except Exception as e:
            print(f"✗ Folder: {folder} - Error: {e}")
    
    # Cek file
    for file in files:
        if os.path.exists(file):
            try:
                os.chmod(file, 0o644)
                print(f"✓ File: {file} - OK")
            except Exception as e:
                print(f"✗ File: {file} - Error: {e}")
        else:
            print(f"⚠ File: {file} - Not found")
    
    # Cek data.xlsx
    data_file = os.path.join(BASE_DIR, "data.xlsx")
    if os.path.exists(data_file):
        try:
            df = pd.read_excel(data_file, nrows=5)
            print(f"✓ data.xlsx readable - Shape: {df.shape}")
        except Exception as e:
            print(f"✗ data.xlsx unreadable - Error: {e}")
    
    print("\n=== Done ===")

if __name__ == "__main__":
    check_and_fix()