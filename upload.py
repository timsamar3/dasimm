# upload.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import pandas as pd
import os
from data_store import load_data, save_data, clear_cache
import traceback

upload_bp = Blueprint("upload", __name__)

# =====================
# PATH AMAN (SERVER)
# =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATA_FILE = os.path.join(BASE_DIR, "data.xlsx")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def validate_excel_columns(df):
    """Validasi kolom minimal yang harus ada"""
    required_cols = ['CLNT_ID', 'CLNT_NAME', 'LINK_ID', 'STN_NAME']
    
    missing_cols = []
    for col in required_cols:
        if col not in df.columns:
            missing_cols.append(col)
    
    return missing_cols

# =====================
# UPLOAD EXCEL
# =====================
@upload_bp.route("/upload", methods=["GET", "POST"])
def upload_excel():
    # 🔐 ADMIN ONLY
    if session.get("role") != "admin":
        flash("Hanya admin yang bisa mengakses halaman ini.", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        file = request.files.get("file")
        mode = request.form.get("mode")

        # ❌ FILE KOSONG
        if not file or file.filename == "":
            flash("File belum dipilih", "danger")
            return redirect(request.url)

        # ❌ FORMAT SALAH
        if not file.filename.lower().endswith((".xlsx", ".xls")):
            flash("File harus berformat .xlsx atau .xls", "danger")
            return redirect(request.url)

        try:
            print(f"Processing upload: {file.filename}, mode: {mode}")
            
            # =====================
            # SIMPAN FILE KE SERVER
            # =====================
            save_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(save_path)
            print(f"File saved to: {save_path}")
            
            # =====================
            # BACA EXCEL
            # =====================
            try:
                df_new = pd.read_excel(save_path, dtype=str, engine="openpyxl")
            except:
                df_new = pd.read_excel(save_path, dtype=str)
            
            print(f"Read Excel - Shape: {df_new.shape}, Columns: {df_new.columns.tolist()}")
            
            # Validasi kolom
            missing_cols = validate_excel_columns(df_new)
            if missing_cols:
                flash(f"Kolom penting tidak ditemukan: {', '.join(missing_cols)}", "danger")
                os.remove(save_path)
                return redirect(request.url)
            
            # Clean data
            df_new = df_new.fillna("")
            
            # Hapus kolom no jika ada
            for c in ["no", "No", "NO"]:
                if c in df_new.columns:
                    df_new = df_new.drop(columns=[c])
            
            print(f"Cleaned data - Shape: {df_new.shape}")
            
            # =====================
            # MODE TAMBAH DATA
            # =====================
            if mode == "append" and os.path.exists(DATA_FILE):
                print("Mode: Append to existing data")
                df_old = load_data()
                
                # Hapus kolom no dari old data
                for c in ["no", "No", "NO"]:
                    if c in df_old.columns:
                        df_old = df_old.drop(columns=[c])
                
                # Gabungkan data
                df_final = pd.concat([df_old, df_new], ignore_index=True)
                print(f"Combined data - Old: {len(df_old)}, New: {len(df_new)}, Final: {len(df_final)}")
                
                flash(f"✅ Data berhasil ditambah. Total: {len(df_final)} baris", "success")

            # =====================
            # MODE UPLOAD ULANG
            # =====================
            elif mode == "reset":
                print("Mode: Reset all data")
                # hapus file data lama
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)

                # hapus semua file di folder uploads
                for f in os.listdir(UPLOAD_FOLDER):
                    file_path = os.path.join(UPLOAD_FOLDER, f)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                
                df_final = df_new
                print(f"New data - Rows: {len(df_final)}")
                flash(f"✅ Data berhasil disimpan (Upload Ulang). Total: {len(df_final)} baris", "success")

            # ❌ MODE TIDAK VALID
            else:
                flash("❌ Mode upload tidak valid", "danger")
                os.remove(save_path)
                return redirect(request.url)

            # =====================
            # SIMPAN DATA
            # =====================
            if save_data(df_final):
                clear_cache()
                print("Data saved successfully")
            else:
                flash("❌ Gagal menyimpan data", "danger")
                return redirect(request.url)

        except Exception as e:
            print(f"Upload error: {str(e)}")
            traceback.print_exc()
            flash(f"❌ Gagal upload: {str(e)}", "danger")
            if os.path.exists(save_path):
                os.remove(save_path)
            return redirect(request.url)

        return redirect(url_for("upload.upload_excel"))

    # GET: Tampilkan halaman upload
    return render_template("upload.html")