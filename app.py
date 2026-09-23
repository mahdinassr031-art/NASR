import os
import sys
import shutil
import hashlib
import tempfile
import subprocess
from base64 import urlsafe_b64encode
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# --- مسیرهای اصلی سیستم ---
APP_NAME = "CompanyDocs_TookaTarh"
BASE_DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), APP_NAME)
DOCS_DIR = os.path.join(BASE_DATA_DIR, "EncryptedDocs")
CONFIG_DIR = os.path.join(BASE_DATA_DIR, "Config")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# رمز پیش‌فرض ادمین: Admin123
DEFAULT_ADMIN_PASS_HASH = hashlib.sha256("Admin123".encode()).hexdigest()
PASS_FILE = os.path.join(CONFIG_DIR, "admin.hash")

if not os.path.exists(PASS_FILE):
    with open(PASS_FILE, "w") as f:
        f.write(DEFAULT_ADMIN_PASS_HASH)

# --- توابع رمزنگاری فایل‌ها ---
def get_cipher_key(password: str) -> bytes:
    salt = b'tooka_tarh_secure_salt_2026'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return urlsafe_b64encode(kdf.derive(password.encode()))

def verify_admin_password(password: str) -> bool:
    with open(PASS_FILE, "r") as f:
        stored_hash = f.read().strip()
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash

# --- کلاس اصلی رابط کاربری (GUI) ---
class TookaTarhApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("سامانه مدیریت اسناد و مدارک - توکا طرح")
        self.geometry("900x650")
        self.configure(bg="#f4f6f9")
        self.setup_ui()

    def setup_ui(self):
        # هدر اصلی
        header_frame = tk.Frame(self, bg="#1e293b", height=80)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            header_frame, 
            text="مدیریت امن مدارک شرکت توکا طرح", 
            font=("Tahoma", 16, "bold"), 
            fg="white", 
            bg="#1e293b"
        )
        title_label.pack(pady=20)

        # پنل دکمه‌ها (ردیف اول)
        btn_frame1 = tk.Frame(self, bg="#f4f6f9")
        btn_frame1.pack(fill=tk.X, padx=20, pady=(15, 5))

        tk.Button(
            btn_frame1, text="➕ افزودن یک مدرک (PDF)", font=("Tahoma", 9, "bold"),
            bg="#22c55e", fg="white", relief=tk.FLAT, padx=10, pady=6,
            command=self.add_single_document
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame1, text="📁 بارگذاری دسته‌جمعی از پوشه", font=("Tahoma", 9, "bold"),
            bg="#0d9488", fg="white", relief=tk.FLAT, padx=10, pady=6,
            command=self.add_folder_documents
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame1, text="❌ حذف مدرک", font=("Tahoma", 9, "bold"),
            bg="#ef4444", fg="white", relief=tk.FLAT, padx=10, pady=6,
            command=self.delete_document
        ).pack(side=tk.RIGHT, padx=5)

        # پنل دکمه‌ها (ردیف دوم)
        btn_frame2 = tk.Frame(self, bg="#f4f6f9")
        btn_frame2.pack(fill=tk.X, padx=20, pady=(5, 10))

        tk.Button(
            btn_frame2, text="👁️ باز کردن/مشاهده مدرک انتخاب‌شده", font=("Tahoma", 9, "bold"),
            bg="#6366f1", fg="white", relief=tk.FLAT, padx=12, pady=6,
            command=self.open_selected_document
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame2, text="📂 باز کردن محل ذخیره‌سازی", font=("Tahoma", 9),
            bg="#0284c7", fg="white", relief=tk.FLAT, padx=10, pady=6,
            command=self.open_file_location
        ).pack(side=tk.LEFT, padx=5)

        # جدول نمایش مدارک
        list_frame = tk.Frame(self, bg="#f4f6f9")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("filename", "size")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("filename", text="نام مدرک")
        self.tree.heading("size", text="حجم (کیلوبایت)")
        self.tree.column("filename", anchor=tk.E, width=550)
        self.tree.column("size", anchor=tk.CENTER, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.refresh_doc_list()

    def prompt_admin_password(self):
        pwd = simpledialog.askstring("احراز هویت ادمین", "لطفاً رمز عبور ادمین را وارد کنید:", show='*')
        if not pwd:
            return None, False
        if verify_admin_password(pwd):
            return pwd, True
        else:
            messagebox.showerror("خطا", "رمز عبور ادمین اشتباه است!")
            return None, False

    def refresh_doc_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for f in os.listdir(DOCS_DIR):
            file_path = os.path.join(DOCS_DIR, f)
            if os.path.isfile(file_path):
                size_kb = round(os.path.getsize(file_path) / 1024, 2)
                display_name = f[:-4] if f.endswith('.enc') else f
                self.tree.insert("", tk.END, values=(display_name, f"{size_kb} KB"))

    def encrypt_and_save_file(self, file_path, admin_pass):
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(DOCS_DIR, file_name + ".enc")
        cipher = Fernet(get_cipher_key(admin_pass))
        with open(file_path, "rb") as f_in:
            data = f_in.read()
        encrypted_data = cipher.encrypt(data)
        with open(dest_path, "wb") as f_out:
            f_out.write(encrypted_data)

    def add_single_document(self):
        admin_pass, auth = self.prompt_admin_password()
        if not auth:
            return

        file_path = filedialog.askopenfilename(
            title="انتخاب فایل PDF",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.encrypt_and_save_file(file_path, admin_pass)
            messagebox.showinfo("موفقیت", "فایل با موفقیت اضافه و رمزنگاری شد.")
            self.refresh_doc_list()
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def add_folder_documents(self):
        admin_pass, auth = self.prompt_admin_password()
        if not auth:
            return

        folder_path = filedialog.askdirectory(title="انتخاب پوشه حاوی فایل‌های PDF")
        if not folder_path:
            return

        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        if not pdf_files:
            messagebox.showwarning("هشدار", "هیچ فایل PDF در پوشه انتخاب‌شده یافت نشد.")
            return

        count = 0
        for f in pdf_files:
            full_path = os.path.join(folder_path, f)
            try:
                self.encrypt_and_save_file(full_path, admin_pass)
                count += 1
            except Exception:
                pass

        messagebox.showinfo("موفقیت", f"تعداد {count} فایل PDF با موفقیت وارد و رمزنگاری گردید.")
        self.refresh_doc_list()

    def open_selected_document(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("هشدار", "لطفاً ابتدا یک مدرک را از لیست انتخاب کنید.")
            return

        admin_pass, auth = self.prompt_admin_password()
        if not auth:
            return

        item_values = self.tree.item(selected_item, "values")
        doc_name = item_values[0]
        enc_file_path = os.path.join(DOCS_DIR, doc_name + ".enc")

        if not os.path.exists(enc_file_path):
            enc_file_path = os.path.join(DOCS_DIR, doc_name)

        try:
            cipher = Fernet(get_cipher_key(admin_pass))
            with open(enc_file_path, "rb") as f_in:
                encrypted_data = f_in.read()
            decrypted_data = cipher.decrypt(encrypted_data)

            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, doc_name)
            with open(temp_file_path, "wb") as f_out:
                f_out.write(decrypted_data)

            os.startfile(temp_file_path)
        except Exception as e:
            messagebox.showerror("خطا در رمزگشایی", "رمز عبور یا فایل رمزنگاری‌شده نامعتبر است.")

    def delete_document(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("هشدار", "لطفاً یک مدرک را از لیست انتخاب کنید.")
            return

        _, auth = self.prompt_admin_password()
        if not auth:
            return

        item_values = self.tree.item(selected_item, "values")
        doc_name = item_values[0]
        file_path = os.path.join(DOCS_DIR, doc_name + ".enc")
        if not os.path.exists(file_path):
            file_path = os.path.join(DOCS_DIR, doc_name)

        if messagebox.askyesno("تایید حذف", f"آیا از حذف مدرک '{doc_name}' اطمینان دارید؟"):
            try:
                os.remove(file_path)
                messagebox.showinfo("حذف شد", "مدرک با موفقیت حذف گردید.")
                self.refresh_doc_list()
            except Exception as e:
                messagebox.showerror("خطا", str(e))

    def open_file_location(self):
        _, auth = self.prompt_admin_password()
        if auth:
            os.startfile(DOCS_DIR)

if __name__ == "__main__":
    app = TookaTarhApp()
    app.mainloop()
