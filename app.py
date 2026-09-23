import os
import sys
import shutil
import hashlib
import tempfile
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

# --- کلاس اصلی برنامه ---
class TookaTarhApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("سامانه مدیریت اسناد و مدارک - توکا طرح")
        self.geometry("1100x720")
        self.configure(bg="#f8fafc")
        self.current_admin_pass = "Admin123"
        self.checked_files = set()  # مجموعه فایل‌های تیک خورده
        self.setup_ui()

    def setup_ui(self):
        # هدر اصلی
        header_frame = tk.Frame(self, bg="#1e293b", height=70)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            header_frame, 
            text="مدیریت امن مدارک شرکت توکا طرح", 
            font=("Tahoma", 16, "bold"), 
            fg="white", 
            bg="#1e293b"
        )
        title_label.pack(pady=15)

        # پنل دکمه‌ها با چینش منظم شبکه (Grid) جهت جلوگیری از له شدن و بهم‌ریختگی دکمه‌ها
        btn_frame = tk.Frame(self, bg="#f8fafc")
        btn_frame.pack(fill=tk.X, padx=15, pady=10)

        for col in range(6):
            btn_frame.columnconfigure(col, weight=1, uniform="btns")

        # دکمه‌های نوار ابزار بالا
        btn_add_file = tk.Button(
            btn_frame, text="➕ افزودن مدرک (ادمین)", font=("Tahoma", 8, "bold"),
            bg="#22c55e", fg="white", relief=tk.FLAT, pady=6, command=self.add_single_document
        )
        btn_add_file.grid(row=0, column=5, padx=3, sticky="nsew")

        btn_add_folder = tk.Button(
            btn_frame, text="📁 بارگذاری از پوشه (ادمین)", font=("Tahoma", 8, "bold"),
            bg="#0d9488", fg="white", relief=tk.FLAT, pady=6, command=self.add_folder_documents
        )
        btn_add_folder.grid(row=0, column=4, padx=3, sticky="nsew")

        btn_delete = tk.Button(
            btn_frame, text="❌ حذف مدرک (ادمین)", font=("Tahoma", 8, "bold"),
            bg="#ef4444", fg="white", relief=tk.FLAT, pady=6, command=self.delete_document
        )
        btn_delete.grid(row=0, column=3, padx=3, sticky="nsew")

        btn_open_loc = tk.Button(
            btn_frame, text="📂 پوشه ذخیره اصلی", font=("Tahoma", 8, "bold"),
            bg="#0284c7", fg="white", relief=tk.FLAT, pady=6, command=self.open_file_location
        )
        btn_open_loc.grid(row=0, column=2, padx=3, sticky="nsew")

        btn_export = tk.Button(
            btn_frame, text="📦 خروجی مدارک انتخاب‌شده", font=("Tahoma", 8, "bold"),
            bg="#eab308", fg="black", relief=tk.FLAT, pady=6, command=self.export_documents
        )
        btn_export.grid(row=0, column=1, padx=3, sticky="nsew")

        btn_view = tk.Button(
            btn_frame, text="👁️ باز کردن / مشاهده", font=("Tahoma", 8, "bold"),
            bg="#6366f1", fg="white", relief=tk.FLAT, pady=6, command=self.open_selected_document
        )
        btn_view.grid(row=0, column=0, padx=3, sticky="nsew")

        # بخش اصلی نمایش دو پنله
        main_container = tk.Frame(self, bg="#f8fafc")
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # پنل چپ: لیست فایل‌ها همراه با چک‌باکس
        left_frame = tk.Frame(paned, bg="#ffffff")
        tk.Label(left_frame, text="📄 لیست کلیه مدارک و فایل‌ها (جهت تغییر تیک، فایل را انتخاب و دکمه پایین را بزنید)", 
                 font=("Tahoma", 9, "bold"), bg="#ffffff", fg="#334155").pack(anchor=tk.E, padx=10, pady=5)

        columns = ("check", "filename", "size")
        self.file_tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        self.file_tree.heading("check", text="انتخاب")
        self.file_tree.heading("filename", text="نام مدرک")
        self.file_tree.heading("size", text="حجم")
        
        self.file_tree.column("check", anchor=tk.CENTER, width=60)
        self.file_tree.column("filename", anchor=tk.E, width=420)
        self.file_tree.column("size", anchor=tk.CENTER, width=100)
        self.file_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # دکمه تغییر وضعیت تیک
        tk.Button(
            left_frame, text="☑️ / ☐ تغییر وضعیت تیک فایل انتخاب‌شده", font=("Tahoma", 9, "bold"),
            bg="#0f766e", fg="white", relief=tk.FLAT, pady=5,
            command=self.toggle_check_selected
        ).pack(fill=tk.X, padx=5, pady=5)

        # پنل راست: لیست پوشه‌ها
        right_frame = tk.Frame(paned, bg="#ffffff")
        tk.Label(right_frame, text="📁 دسته پوشه‌ها", font=("Tahoma", 9, "bold"), bg="#ffffff", fg="#334155").pack(anchor=tk.E, padx=10, pady=5)
        
        self.folder_tree = ttk.Treeview(right_frame, show="tree", selectmode="browse")
        self.folder_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # جایگزین دستور خطاساز bind با یک دکمه کاملا ایمن
        tk.Button(
            right_frame, text="نمایش فایل‌های این پوشه", font=("Tahoma", 9, "bold"),
            bg="#3b82f6", fg="white", relief=tk.FLAT, pady=5,
            command=self.on_folder_select_btn
        ).pack(fill=tk.X, padx=5, pady=5)

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
        self.update_file_list("همه مدارک")

    def on_folder_select_btn(self):
        selected_item = self.folder_tree.selection()
        if selected_item:
            folder_name = self.folder_tree.item(selected_item[0], "text")
            self.update_file_list(folder_name)
        else:
            self.update_file_list("همه مدارک")

    def update_file_list(self, folder_name):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        for f in os.listdir(DOCS_DIR):
            if f.endswith('.enc'):
                file_path = os.path.join(DOCS_DIR, f)
                size_kb = round(os.path.getsize(file_path) / 1024, 2)
                
                show_file = False
                if folder_name == "همه مدارک":
                    show_file = True
                    display_name = f.replace('.enc', '').rsplit('__', 1)[-1]
                elif f.startswith(folder_name + "__"):
                    show_file = True
                    display_name = f.replace('.enc', '').replace(folder_name + "__", "")

                if show_file:
                    check_icon = "☑" if f in self.checked_files else "☐"
                    self.file_tree.insert("", tk.END, values=(check_icon, display_name, f"{size_kb} KB", f))

    def toggle_check_selected(self):
        selected_item = self.file_tree.selection()
        if not selected_item:
            messagebox.showwarning("راهنما", "لطفاً ابتدا یک فایل را از لیست انتخاب کنید.")
            return

        values = self.file_tree.item(selected_item[0], "values")
        if not values or len(values) < 4:
            return

        real_enc_filename = values[3]
        if real_enc_filename in self.checked_files:
            self.checked_files.remove(real_enc_filename)
            new_icon = "☐"
        else:
            self.checked_files.add(real_enc_filename)
            new_icon = "☑"

        self.file_tree.item(selected_item[0], values=(new_icon, values[1], values[2], values[3]))

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

        file_path = filedialog.askopenfilename(
            title="انتخاب فایل مدرک (تصویر، فایل ورد، اکسل، PDF و غیره)", 
            filetypes=[("All Files", "*.*")]
        )
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

        folder_path = filedialog.askdirectory(title="انتخاب پوشه حاوی مدارک")
        if not folder_path:
            return

        folder_name = os.path.basename(folder_path)
        all_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        if not all_files:
            messagebox.showwarning("هشدار", "هیچ فایلی در پوشه پیدا نشد.")
            return

        count = 0
        for f in all_files:
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
        real_enc_filename = item_values[3] if len(item_values) > 3 else item_values[1] + ".enc"
        enc_path = os.path.join(DOCS_DIR, real_enc_filename)

        try:
            cipher = Fernet(get_cipher_key("Admin123"))
            with open(enc_path, "rb") as f_in:
                data = f_in.read()
            decrypted = cipher.decrypt(data)

            temp_file = os.path.join(tempfile.gettempdir(), item_values[1])
            with open(temp_file, "wb") as f_out:
                f_out.write(decrypted)

            os.startfile(temp_file)
        except Exception:
            messagebox.showerror("خطا", "رمزگشایی یا باز کردن فایل با خطا مواجه شد.")

    def export_documents(self):
        if not self.checked_files:
            messagebox.showwarning("هشدار", "هیچ مدرکی تیک نخورده است! لطفاً ابتدا مدارک موردنظر را تیک بزنید.")
            return

        export_dir = filedialog.askdirectory(title="انتخاب محل ذخیره خروجی مدارک")
        if not export_dir:
            return

        success_count = 0
        cipher = Fernet(get_cipher_key("Admin123"))

        for enc_filename in list(self.checked_files):
            enc_path = os.path.join(DOCS_DIR, enc_filename)
            if not os.path.exists(enc_path):
                continue

            display_name = enc_filename.replace('.enc', '').rsplit('__', 1)[-1]
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

        messagebox.showinfo("خروجی موفق", f"تعداد {success_count} مدرک انتخاب‌شده با فرمت اصلی‌شان در پوشه مقصد ذخیره شدند.")

    def delete_document(self):
        selected_items = self.file_tree.selection()
        if not selected_items:
            messagebox.showwarning("هشدار", "لطفاً یک مدرک را جهت حذف انتخاب کنید.")
            return

        if not self.prompt_admin_password():
            return

        item_values = self.file_tree.item(selected_items[0], "values")
        real_enc_filename = item_values[3] if len(item_values) > 3 else item_values[1] + ".enc"
        file_path = os.path.join(DOCS_DIR, real_enc_filename)

        if messagebox.askyesno("تایید حذف", "آیا از حذف این مدرک اطمینان دارید؟"):
            try:
                os.remove(file_path)
                if real_enc_filename in self.checked_files:
                    self.checked_files.remove(real_enc_filename)
                messagebox.showinfo("حذف شد", "مدرک با موفقیت حذف شد.")
                self.refresh_folders()
            except Exception as e:
                messagebox.showerror("خطا", str(e))

    def open_file_location(self):
        os.startfile(DOCS_DIR)

if __name__ == "__main__":
    app = TookaTarhApp()
    app.mainloop()
