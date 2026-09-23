import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import openpyxl

class GearCostApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GearCost Pro - سیستم برآورد قیمت گیربکس و چرخ‌دنده")
        self.root.geometry("750x650")
        self.root.configure(bg="#1e1e1e")

        # Style Configuration
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#1e1e1e", foreground="#ffffff", fieldbackground="#2d2d2d")
        style.configure("TLabel", font=("Tahoma", 10), background="#1e1e1e", foreground="#ffffff")
        style.configure("TButton", font=("Tahoma", 10, "bold"), background="#0e639c", foreground="#ffffff")
        style.map("TButton", background=[("active", "#1177bb")])

        # Header
        header = tk.Label(root, text="⚙️ GearCost Pro (نسخه دسکتاپ)", font=("Tahoma", 16, "bold"), bg="#252526", fg="#007acc", py=10)
        header.pack(fill="x")

        # Main Container
        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(fill="both", expand=True)

        # Inputs Section
        inputs_frame = ttk.LabelFrame(main_frame, text=" ورودی‌های چرخ‌دنده ", padding="10")
        inputs_frame.pack(fill="x", pady=5)

        # Grid Inputs
        ttk.Label(inputs_frame, text="مدول (m):").grid(row=0, column=0, sticky="w", pady=5)
        self.m_entry = ttk.Entry(inputs_frame)
        self.m_entry.insert(0, "4.0")
        self.m_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(inputs_frame, text="تعداد دنده (z):").grid(row=0, column=2, sticky="w", pady=5)
        self.z_entry = ttk.Entry(inputs_frame)
        self.z_entry.insert(0, "30")
        self.z_entry.grid(row=0, column=3, padx=10, pady=5)

        ttk.Label(inputs_frame, text="پهنای دنده - mm (b):").grid(row=1, column=0, sticky="w", pady=5)
        self.b_entry = ttk.Entry(inputs_frame)
        self.b_entry.insert(0, "40.0")
        self.b_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(inputs_frame, text="نوع متریال:").grid(row=1, column=2, sticky="w", pady=5)
        self.mat_combo = ttk.Combobox(inputs_frame, values=["MO40", "VCN150", "CK45", "چدن"], state="readonly")
        self.mat_combo.current(0)
        self.mat_combo.grid(row=1, column=3, padx=10, pady=5)

        ttk.Label(inputs_frame, text="قیمت متریال (ریال/کیلو):").grid(row=2, column=0, sticky="w", pady=5)
        self.mat_price_entry = ttk.Entry(inputs_frame)
        self.mat_price_entry.insert(0, "950000")
        self.mat_price_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(inputs_frame, text="نرخ تراشکاری (ریال/ساعت):").grid(row=2, column=2, sticky="w", pady=5)
        self.labor_price_entry = ttk.Entry(inputs_frame)
        self.labor_price_entry.insert(0, "2500000")
        self.labor_price_entry.grid(row=2, column=3, padx=10, pady=5)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)

        calc_btn = ttk.Button(btn_frame, text="🧮 محاسبه آنالیز قیمت", command=self.calculate)
        calc_btn.pack(side="left", padx=5)

        excel_btn = ttk.Button(btn_frame, text="📥 خروجی اکسل (.xlsx)", command=self.export_excel)
        excel_btn.pack(side="left", padx=5)

        # Output Treeview
        self.tree = ttk.Treeview(main_frame, columns=("item", "qty", "unit_price", "total"), show="headings", height=8)
        self.tree.heading("item", text="شرح هزینه / پارامتر")
        self.tree.heading("qty", text="مقدار / زمان")
        self.tree.heading("unit_price", text="نرخ واحد (ریال)")
        self.tree.heading("total", text="مجموع (ریال)")
        self.tree.pack(fill="both", expand=True, pady=10)

        # Result Total
        self.result_label = tk.Label(main_frame, text="قیمت نهایی: ۰ ریال", font=("Tahoma", 14, "bold"), bg="#1e1e1e", fg="#4ec9b0")
        self.result_label.pack(anchor="e", pady=5)

    def calculate(self):
        try:
            m = float(self.m_entry.get())
            z = int(self.z_entry.get())
            b = float(self.b_entry.get())
            mat_price = float(self.mat_price_entry.get())
            labor_price = float(self.labor_price_entry.get())

            # هندسه و وزن
            da = (z + 2) * m
            vol = (math.pi / 4) * (da ** 2) * b
            weight_net = vol * 7.85e-6
            weight_gross = weight_net * 1.15  # ۱۵ درصد پرت

            # هزینه‌ها
            cost_mat = weight_gross * mat_price
            time_turn = 0.3 + (da * b) / 15000
            time_hob = 0.2 + (z * m * b) / 12000
            cost_labor = (time_turn + time_hob) * labor_price
            
            subtotal = cost_mat + cost_labor
            final_total = subtotal * 1.20  # ۲۰ درصد سود و سربار

            # پاکسازی جدول
            for row in self.tree.get_children():
                self.tree.delete(row)

            self.tree.insert("", "end", values=("وزن خالص قطعه", f"{weight_net:.2f} kg", "-", "-"))
            self.tree.insert("", "end", values=(f"متریال خام ({self.mat_combo.get()})", f"{weight_gross:.2f} kg", f"{mat_price:,.0f}", f"{cost_mat:,.0f}"))
            self.tree.insert("", "end", values=("تراشکاری و دنده‌زنی", f"{time_turn+time_hob:.2f} ساعت", f"{labor_price:,.0f}", f"{cost_labor:,.0f}"))
            self.tree.insert("", "end", values=("سربار و سود کارخانه (20%)", "-", "-", f"{subtotal*0.20:,.0f}"))

            self.result_label.config(text=f"قیمت نهایی: {final_total:,.0f} ریال")
            self.last_data = {"m": m, "z": z, "b": b, "final": final_total, "mat_cost": cost_mat, "labor_cost": cost_labor}

        except Exception as e:
            messagebox.showerror("خطا", f"لطفاً ورودی‌ها را بررسی کنید:\n{e}")

    def export_excel(self):
        if not hasattr(self, 'last_data'):
            messagebox.showwarning("هشدار", "ابتدا دکمه محاسبه را بزنید.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "آنالیز قیمت"
            ws.views.sheetView[0].rightToLeft = True

            ws.append(["شرح", "مقدار"])
            ws.append(["مدول", self.last_data["m"]])
            ws.append(["تعداد دنده", self.last_data["z"]])
            ws.append(["هزینه متریال (ریال)", self.last_data["mat_cost"]])
            ws.append(["هزینه دستمزد (ریال)", self.last_data["labor_cost"]])
            ws.append(["قیمت کل نهایی (ریال)", self.last_data["final"]])

            wb.save(file_path)
            messagebox.showinfo("موفقیت", "فایل اکسل با موفقیت ذخیره شد.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GearCostApp(root)
    root.mainloop()
