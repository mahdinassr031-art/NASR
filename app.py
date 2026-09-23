import os
import sys
import shutil
import hashlib
import tempfile
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from base64 import urlsafe_b64encode
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

# --- توابع رمزنگاری ---
MASTER_KEY = b'tooka_tarh_secure_salt_2026'

def get_cipher_key(password: str = "Admin123") -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=MASTER_KEY,
        iterations=100000,
    )
    return urlsafe_b64encode(kdf.derive(password.encode()))

def verify_admin_password(password: str) -> bool:
    with open(PASS_FILE, "r") as f:
        stored_hash = f.read().strip()
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash

# --- رسم لوگوی گرافیکی چرخ‌دنده و پرنده توکا ---
def draw_tooka_logo(canvas, cx, cy, radius):
    canvas.delete("all")
    teeth = 12
    outer_r = radius
    inner_r = radius * 0.75
    gear_pts = []
    
    for i in range(teeth * 2):
        angle = i * math.pi / teeth
        r = outer_r if i % 2 == 0 else inner_r
        gear_pts.append(cx + r * math.cos(angle))
        gear_pts.append(cy + r * math.sin(angle))
        
    canvas.create_polygon(gear_pts, fill="#f1f5f9", outline="#cbd5e1", width=2)
    canvas.create_oval(cx - inner_r * 0.5, cy - inner_r * 0.5, cx + inner_r * 0.5, cy + inner_r * 0.5, fill="#ffffff", outline="#cbd5e1")

    bird_pts = [
        cx - radius * 0.2, cy + radius * 0.1,
        cx - radius * 0.1, cy - radius * 0.2,
        cx + radius * 0.1, cy - radius * 0.25,
        cx + radius * 0.35, cy - radius * 0.15,
        cx + radius * 0.15, cy + radius * 0.1,
        cx + radius * 0.25, cy + radius * 0.3,
        cx, cy + radius * 0.2,
    ]
    canvas.create_polygon(bird_pts, fill="#3b82f6", outline="#1d4ed8")
    canvas.create_polygon([cx + radius * 0.35, cy - radius * 0.15, cx + radius * 0.48, cy - radius * 0.1, cx + radius * 0.32, cy - radius * 0.05], fill="#f59e0b")

# --- کلاس اصلی برنامه ---
class TookaTarhApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("سامانه مدیریت اسناد و مدارک - توکا طرح")
        self.geometry("1000x700")
        self.configure(bg="#f8fafc")
        self.current_admin_pass = "Admin123"
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

        # پنل دکمه‌ها
        btn_frame = tk.Frame(self, bg="#f8fafc")
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        # دکمه‌های نیازمند رمز ادمین (سمت راست)
        tk.Button(
            btn_frame, text="➕ افزودن مدرک (ادمین)", font=("Tahoma", 9, "bold"),
            bg="#22c55e", fg="white", relief=tk.FLAT, padx=10, pady=6,
            command=self.add_single_document
        ).pack(side=tk.RIGHT, padx=4)

        tk.Button(
            btn_frame, text="📁 بارگذاری از پوشه (ادمین)", font=("Tahoma", 9, "bold"),
            bg="#0d9488", fg="white", relief=tk.FLAT, padx=10, pady=6,
            command=self.add_folder_documents
        ).pack(side=tk.RIGHT, padx=4)

        tk.Button(
            btn_frame, text="❌ حذف مدرک (ادمین)", font=("Tahoma", 9, "bold"),
            bg="#ef4444", fg="white", relief=tk.FLAT, padx=10, pady=6,
            command=self.delete_document
        ).pack(side=tk.RIGHT, padx=4)

        # دکمه‌های عمومی بدون نیاز به رمز (سمت چپ)
        tk.Button(
            btn_frame, text="👁️ باز کردن / مشاهده", font=("Tahoma", 9, "bold"),
            bg="#6366f1", fg="white", relief=tk.FLAT, padx=10, pady=6,
            command=self.open_selected_document
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            btn_frame, text="📦 خروجی مدارک برای پروژه", font=("Tahoma", 9, "bold"),
            bg="#eab308", fg="black", relief=tk.FLAT, padx=10, pady=6,
            command=self.export_documents
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            btn_frame, text="📂 پوشه ذخیره", font=("Tahoma", 9),
            bg="#0284c7", fg="white", relief=tk.FLAT, padx=10, pady=6,
            command=self.open_file_location
        ).pack(side=tk.LEFT, padx=4)

        # بخش اصلی نمایش دو پنله
        main_container = tk.Frame(self, bg="#f8fafc")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # پنل راست: لیست پوشه‌ها
        right_frame = tk.Frame(paned, bg="#ffffff")
        tk.Label(right_frame, text="📁 دسته پوشه‌ها", font=("Tahoma", 10, "bold"), bg="#ffffff", fg="#334155").pack(anchor=tk.E, padx=10, pady=5)
        
        self.folder_tree = ttk.Treeview(right_frame, show="tree", selectmode="browse")
        self.folder_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.folder_tree.bind("<>", self.on_folder_select)

        # پنل چپ: لیست فایل‌های PDF
        left_frame = tk.Frame(paned, bg="#ffffff")
        tk.Label(left_frame, text="📄 فایل‌های PDF داخل پوشه", font=("Tahoma", 10, "bold"), bg="#ffffff", fg="#334155").pack(anchor=tk.E, padx=10, pady=5)

        columns = ("filename", "size")
        self.file_tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="extended")
        self.file_tree.heading("filename", text="نام مدرک")
        self.file_tree.heading("size", text="حجم")
        self.file_tree.column("filename", anchor=tk.E, width=400)
        self.file_tree.column("size", anchor=tk.CENTER, width=120)
        self.file_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        paned.add(left_frame, weight=3)
        paned.add(right_frame, weight=1)

        self.refresh_folders()

    def prompt_admin_password(self):
        pwd = simpledialog.askstring("احراز هویت ادمین", "لطفاً رمز عبور ادمین را وارد کنید:", show='*')
        if not pwd:
            return False
        if verify_admin_password(pwd):
            self.current_admin_pass = pwd
            return True
        else:
            messagebox.showerror("خطا", "رمز عبور ادمین اشتباه است!")
            return False

    def refresh_folders(self):
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)

        root_node = self.folder_tree.insert("", tk.END, text="همه مدارک", open=True)
        
        folders = set()
        for f in os.listdir(DOCS_DIR):
            if f.endswith('.enc'):
                parts = f.split('__')
                if len(parts) > 1:
                    folders.add(parts[0])

        for folder in sorted(folders):
            self.folder_tree.insert(root_node, tk.END, text=folder)

        self.folder_tree.selection_set(root_node)

    def on_folder_select(self, event):
        selected_item = self.folder_tree.selection()
        if not selected_item:
            return

        folder_name = self.folder_tree.item(selected_item[0], "text")
        
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        for f in os.listdir(DOCS_DIR):
            if f.endswith('.enc'):
                file_path = os.path.join(DOCS_DIR, f)
                size_kb = round(os.path.getsize(file_path) / 1024, 2)
                
                if folder_name == "همه مدارک":
                    display_name = f.replace('.enc', '').rsplit('__', 1)[-1]
                    self.file_tree.insert("", tk.END, values=(display_name, f"{size_kb} KB", f))
                else:
                    if f.startswith(folder_name + "__"):
                        display_name = f.replace('.enc', '').replace(folder_name + "__", "")
                        self.file_tree.insert("", tk.END, values=(display_name, f"{size_kb} KB", f))

    def encrypt_and_save(self, src_path, target_folder="عمومی"):
        file_name = os.path.basename(src_path)
        enc_name = f"{target_folder}__{file_name}.enc"
        dest_path = os.path.join(DOCS_DIR, enc_name)

        cipher = Fernet(get_cipher_key(self.current_admin_pass))
        with open(src_path, "rb") as f_in:
            data = f_in.read()
        encrypted_data = cipher.encrypt(data)
        
        with open(dest_path, "wb") as f_out:
            f_out.write(encrypted_data)

    def add_single_document(self):
        if not self.prompt_admin_password():
            return

        file_path = filedialog.askopenfilename(title="انتخاب فایل PDF", filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return

        folder_name = simpledialog.askstring("نام پوشه", "نام پوشه/دسته‌بندی را وارد کنید:", initialvalue="عمومی")
        if not folder_name:
            folder_name = "عمومی"

        try:
            self.encrypt_and_save(file_path, folder_name)
            messagebox.showinfo("موفقیت", "فایل با موفقیت رمزنگاری و اضافه شد.")
            self.refresh_folders()
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def add_folder_documents(self):
        if not self.prompt_admin_password():
            return

        folder_path = filedialog.askdirectory(title="انتخاب پوشه حاوی PDF")
        if not folder_path:
            return

        folder_name = os.path.basename(folder_path)
        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]

        if not pdf_files:
            messagebox.showwarning("هشدار", "هیچ فایل PDF پیدا نشد.")
            return

        count = 0
        for f in pdf_files:
            try:
                self.encrypt_and_save(os.path.join(folder_path, f), folder_name)
                count += 1
            except Exception:
                pass

        messagebox.showinfo("موفقیت", f"تعداد {count} فایل در پوشه '{folder_name}' بارگذاری شد.")
        self.refresh_folders()

    def open_selected_document(self):
        selected_items = self.file_tree.selection()
        if not selected_items:
            messagebox.showwarning("هشدار", "لطفاً یک فایل را انتخاب کنید.")
            return

        item_values = self.file_tree.item(selected_items[0], "values")
        real_enc_filename = item_values[2] if len(item_values) > 2 else item_values[0] + ".enc"
        enc_path = os.path.join(DOCS_DIR, real_enc_filename)

        try:
            cipher = Fernet(get_cipher_key("Admin123"))
            with open(enc_path, "rb") as f_in:
                data = f_in.read()
            decrypted = cipher.decrypt(data)

            temp_file = os.path.join(tempfile.gettempdir(), item_values[0])
            with open(temp_file, "wb") as f_out:
                f_out.write(decrypted)

            os.startfile(temp_file)
        except Exception:
            messagebox.showerror("خطا", "رمزگشایی فایل با خطا مواجه شد.")

    def export_documents(self):
        selected_items = self.file_tree.selection()
        if not selected_items:
            messagebox.showwarning("هشدار", "لطفاً مدرک یا مدارک مورد نظر جهت خروجی را از لیست سمت چپ انتخاب کنید.")
            return

        export_dir = filedialog.askdirectory(title="انتخاب محل ذخیره خروجی پروژه")
        if not export_dir:
            return

        success_count = 0
        cipher = Fernet(get_cipher_key("Admin123"))

        for item in selected_items:
            item_values = self.file_tree.item(item, "values")
            display_name = item_values[0]
            real_enc_filename = item_values[2] if len(item_values) > 2 else display_name + ".enc"
            enc_path = os.path.join(DOCS_DIR, real_enc_filename)

            try:
                with open(enc_path, "rb") as f_in:
                    data = f_in.read()
                decrypted = cipher.decrypt(data)

                out_path = os.path.join(export_dir, display_name)
                with open(out_path, "wb") as f_out:
                    f_out.write(decrypted)
                success_count += 1
            except Exception:
                pass

        messagebox.showinfo("خروجی موفق", f"تعداد {success_count} مدرک با موفقیت در پوشه انتخاب‌شده ذخیره گردید.")

    def delete_document(self):
        selected_items = self.file_tree.selection()
        if not selected_items:
            messagebox.showwarning("هشدار", "لطفاً یک مدرک را جهت حذف انتخاب کنید.")
            return

        if not self.prompt_admin_password():
            return

        item_values = self.file_tree.item(selected_items[0], "values")
        real_enc_filename = item_values[2] if len(item_values) > 2 else item_values[0] + ".enc"
        file_path = os.path.join(DOCS_DIR, real_enc_filename)

        if messagebox.askyesno("تایید حذف", "آیا از حذف این مدرک اطمینان دارید؟"):
            try:
                os.remove(file_path)
                messagebox.showinfo("حذف شد", "مدرک با موفقیت حذف شد.")
                self.refresh_folders()
            except Exception as e:
                messagebox.showerror("خطا", str(e))

    def open_file_location(self):
        os.startfile(DOCS_DIR)

if __name__ == "__main__":
    app = TookaTarhApp()
    app.mainloop()
