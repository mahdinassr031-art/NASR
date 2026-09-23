import os, sys, hashlib
from base64 import urlsafe_b64encode
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

APP_NAME = "CompanyDocs_TookaTarh"
BASE_DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), APP_NAME)
DOCS_DIR = os.path.join(BASE_DATA_DIR, "EncryptedDocs")
CONFIG_DIR = os.path.join(BASE_DATA_DIR, "Config")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

class TookaTarhApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("سامانه مدیریت اسناد و مدارک - توکا طرح")
        self.geometry("800x600")
        label = tk.Label(self, text="سامانه مدیریت مدارک شرکت توکا طرح", font=("Tahoma", 14))
        label.pack(pady=50)

if __name__ == "__main__":
    app = TookaTarhApp()
    app.mainloop()
