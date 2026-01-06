from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
import pandas as pd
from functools import wraps
from data_store import load_data, save_data, clear_cache
import traceback
import json

admin_data_bp = Blueprint("admin_data", __name__, url_prefix="/admin")

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Akses admin diperlukan", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return wrapper


# =====================
# HALAMAN DATA ADMIN
# =====================
@admin_data_bp.route("/data")
@admin_required
def data_table():
    try:
        df = load_data().copy()
        print(f"Admin page - Loaded {len(df)} rows")
        
        # Pastikan ada kolom no
        if "no" not in df.columns and len(df) > 0:
            df.insert(0, "no", range(1, len(df) + 1))
        
        columns = df.columns.tolist()
        print(f"Admin columns: {columns}")
        
        return render_template("data_admin.html", columns=columns)
        
    except Exception as e:
        print(f"Error in admin page: {e}")
        traceback.print_exc()
        return render_template("data_admin.html", columns=["no", "Aksi"])


# =====================
# API DATATABLES - UPDATE UNTUK POST METHOD
# =====================
@admin_data_bp.route("/data/json", methods=["GET", "POST"])  # TAMBAHKAN POST METHOD
@admin_required
def api():
    try:
        # Load data
        df = load_data().copy()
        print(f"Admin API - Loaded {len(df)} rows")
        
        if df.empty:
            print("Admin API - DataFrame is empty")
            return jsonify({
                "draw": 1,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": []
            })
        
        # Pastikan ada kolom no
        if "no" not in df.columns and len(df) > 0:
            df.insert(0, "no", range(1, len(df) + 1))
        
        # PERBAIKAN: Pastikan SEMUA kolom adalah string sebelum pencarian
        df = df.astype(str)
        
        # Get Datatable parameters dari POST atau GET
        if request.method == "POST":
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form
        else:
            data = request.args
            
        if not data:
            data = {}
        
        # Ambil parameter DataTables
        draw = int(data.get("draw", 1))
        start = int(data.get("start", 0))
        length = int(data.get("length", 25))
        search = data.get("search[value]", "").strip()
        print(f"Admin API params - method:{request.method}, draw:{draw}, start:{start}, length:{length}, search:'{search}'")
        
        # Apply filter jika ada search
        if search:
            print(f"Applying search filter: '{search}'")
            # Convert search ke lowercase
            search_lower = search.lower()
            
            # PERBAIKAN: Buat mask dengan cara yang aman untuk string
            mask = pd.Series([False] * len(df), index=df.index)
            
            for col in df.columns:
                # Gunakan metode yang aman untuk pencarian string
                col_data = df[col].astype(str)
                mask = mask | col_data.str.lower().str.contains(search_lower, na=False)
            
            filtered = df[mask]
            print(f"Search result: {len(filtered)} rows found")
        else:
            filtered = df
        
        # Pagination
        total_records = len(df)
        total_filtered = len(filtered)
        page_df = filtered.iloc[start:start + length] if total_filtered > 0 else pd.DataFrame()
        
        # Prepare response data
        data = []
        for _, row in page_df.iterrows():
            row_data = row.to_dict()
            
            # Tambahkan tombol aksi (gunakan nomor dari kolom 'no')
            try:
                no_value = str(row_data.get('no', ''))
                if no_value and no_value.isdigit():
                    no_int = int(no_value)
                    row_data["aksi"] = f"""
                        <a href="{url_for('admin_data.edit_data', no=no_int)}"
                           class="btn btn-warning btn-sm mr-1"
                           title="Edit">
                           ✏️
                        </a>
                        <a href="{url_for('admin_data.hapus_data', no=no_int)}"
                           class="btn btn-danger btn-sm delete-btn"
                           title="Hapus"
                           onclick="return confirm('Yakin hapus data ini?')">
                           🗑️
                        </a>
                    """
                else:
                    row_data["aksi"] = "<span class='text-muted'>-</span>"
            except:
                row_data["aksi"] = "<span class='text-muted'>-</span>"
            
            # Convert semua values ke string
            row_data = {k: str(v) if v is not None else "" for k, v in row_data.items()}
            data.append(row_data)
        
        print(f"Admin API - Returning {len(data)} rows")
        
        response = {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in admin API: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        }), 500


# =====================
# EDIT & HAPUS
# =====================
@admin_data_bp.route("/edit/<int:no>", methods=["GET", "POST"])
@admin_required
def edit_data(no):
    try:
        df = load_data()
        
        # Validasi nomor
        if no < 1 or no > len(df):
            flash("Data tidak ditemukan", "danger")
            return redirect(url_for("admin_data.data_table"))
        
        if request.method == "POST":
            # Update data
            for col in df.columns:
                if col != "no":  # Skip kolom no
                    new_value = request.form.get(col, "").strip()
                    df.at[no - 1, col] = new_value
            
            # Simpan perubahan
            if save_data(df):
                clear_cache()
                flash("Data berhasil diperbarui", "success")
            else:
                flash("Gagal menyimpan data", "danger")
            
            return redirect(url_for("admin_data.data_table"))
        
        # GET: Tampilkan form edit
        data = df.iloc[no - 1].to_dict()
        return render_template("data_edit.html", data=data, no=no)
        
    except Exception as e:
        print(f"Error in edit_data: {e}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("admin_data.data_table"))


@admin_data_bp.route("/hapus/<int:no>")
@admin_required
def hapus_data(no):
    try:
        df = load_data()
        
        if no < 1 or no > len(df):
            flash("Data tidak ditemukan", "danger")
            return redirect(url_for("admin_data.data_table"))
        
        # Hapus baris
        df = df.drop(df.index[no - 1]).reset_index(drop=True)
        
        # Reset nomor urut
        if "no" in df.columns:
            df["no"] = range(1, len(df) + 1)
        
        # Simpan
        if save_data(df):
            clear_cache()
            flash("Data berhasil dihapus", "success")
        else:
            flash("Gagal menghapus data", "danger")
        
        return redirect(url_for("admin_data.data_table"))
        
    except Exception as e:
        print(f"Error in hapus_data: {e}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("admin_data.data_table"))


# =====================
# DEBUG ENDPOINT
# =====================
@admin_data_bp.route("/debug")
@admin_required
def debug():
    from data_store import get_data_info
    info = get_data_info()
    return jsonify(info)


# =====================
# FALLBACK API GET (UNTUK KOMPATIBILITAS)
# =====================
@admin_data_bp.route("/data/json-get", methods=["GET"])  # API GET alternatif
@admin_required
def api_get():
    """Alternatif API dengan GET untuk kompatibilitas"""
    try:
        # Load data
        df = load_data().copy()
        print(f"Admin API GET - Loaded {len(df)} rows")
        
        if df.empty:
            return jsonify({
                "draw": 1,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": []
            })
        
        # Pastikan ada kolom no
        if "no" not in df.columns and len(df) > 0:
            df.insert(0, "no", range(1, len(df) + 1))
        
        # Pastikan semua string
        df = df.astype(str)
        
        # Get parameters
        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = int(request.args.get("length", 25))
        search = request.args.get("search[value]", "").strip()
        
        # Batasi panjang search untuk menghindari 414 error
        if len(search) > 1000:
            search = search[:1000]
            print(f"Search truncated to 1000 characters")
        
        print(f"Admin API GET params - draw:{draw}, start:{start}, length:{length}, search:'{search}'")
        
        # Apply filter jika ada search
        if search:
            search_lower = search.lower()
            mask = pd.Series([False] * len(df), index=df.index)
            
            for col in df.columns:
                col_data = df[col].astype(str)
                mask = mask | col_data.str.lower().str.contains(search_lower, na=False)
            
            filtered = df[mask]
        else:
            filtered = df
        
        # Pagination
        total_records = len(df)
        total_filtered = len(filtered)
        page_df = filtered.iloc[start:start + length] if total_filtered > 0 else pd.DataFrame()
        
        # Prepare response data
        data = []
        for _, row in page_df.iterrows():
            row_data = row.to_dict()
            
            try:
                no_value = str(row_data.get('no', ''))
                if no_value and no_value.isdigit():
                    no_int = int(no_value)
                    row_data["aksi"] = f"""
                        <a href="{url_for('admin_data.edit_data', no=no_int)}"
                           class="btn btn-warning btn-sm mr-1"
                           title="Edit">
                           ✏️
                        </a>
                        <a href="{url_for('admin_data.hapus_data', no=no_int)}"
                           class="btn btn-danger btn-sm delete-btn"
                           title="Hapus"
                           onclick="return confirm('Yakin hapus data ini?')">
                           🗑️
                        </a>
                    """
                else:
                    row_data["aksi"] = "<span class='text-muted'>-</span>"
            except:
                row_data["aksi"] = "<span class='text-muted'>-</span>"
            
            row_data = {k: str(v) if v is not None else "" for k, v in row_data.items()}
            data.append(row_data)
        
        print(f"Admin API GET - Returning {len(data)} rows")
        
        response = {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in admin API GET: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        }), 500