import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
from PIL import Image, ImageTk
from fpdf import FPDF
import sqlite3
import os
from datetime import datetime
import shutil

# ---------------- Setup Paths ----------------
user_folder = os.path.join(os.path.expanduser("~"), "NumerologyDashboard")
os.makedirs(user_folder, exist_ok=True)
backup_folder = os.path.join(user_folder, "backups")
os.makedirs(backup_folder, exist_ok=True)

db_path = os.path.join(user_folder, "numerology_remedies.db")
default_logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
user_logo_path = os.path.join(user_folder, "user_logo.png")
logo_path = user_logo_path if os.path.exists(user_logo_path) else default_logo_path

# If bundled default DB isn't present in the user folder, copy the shipped one
shipped_db = os.path.join(os.path.dirname(__file__), "numerology_remedies.db")
if not os.path.exists(db_path) and os.path.exists(shipped_db):
    shutil.copy(shipped_db, db_path)

# ---------------- Database ----------------
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS remedies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER NOT NULL,
    grid_type TEXT NOT NULL,
    category TEXT NOT NULL,
    text TEXT NOT NULL
)
""")
conn.commit()

# ---------------- Numerology Logic ----------------
default_remedies = {
    1: "Leadership, Red, Sun mantra",
    2: "Patience, White, Moon mantra",
    3: "Creativity, Yellow, Jupiter mantra",
    4: "Stability, Green, Rahu mantra",
    5: "Freedom, Blue, Mercury mantra",
    6: "Harmony, Indigo, Venus mantra",
    7: "Spirituality, Violet, Ketu mantra",
    8: "Success, Gray, Saturn mantra",
    9: "Wisdom, Orange, Mars mantra"
}

def letter_to_number(letter):
    mapping = {'A':1,'J':1,'S':1,'B':2,'K':2,'T':2,'C':3,'L':3,'U':3,'D':4,'M':4,'V':4,'E':5,'N':5,'W':5,'F':6,'O':6,'X':6,'G':7,'P':7,'Y':7,'H':8,'Q':8,'Z':8,'I':9,'R':9}
    return mapping.get(letter.upper(),0)

def calculate_name_number(name):
    total = sum([letter_to_number(c) for c in name if c.isalpha()])
    while total>9: total=sum([int(x) for x in str(total)])
    return total

def calculate_birth_number(dob):
    total=sum([int(x) for x in dob if x.isdigit()])
    while total>9: total=sum([int(x) for x in str(total)])
    return total

def generate_loshu_grid(dob):
    digits=[int(d) for d in dob if d.isdigit()]
    grid={i:digits.count(i) for i in range(1,10)}
    return grid

def analyze_loshu_grid(grid):
    analysis={}
    for num,count in grid.items():
        if count==0: analysis[num]="Missing number – work on this trait"
        elif count>1: analysis[num]="Repeated number – strong influence"
        else: analysis[num]="Balanced number"
    return analysis

def generate_vedic_grid(dob,name):
    birth_num=calculate_birth_number(dob)
    name_num=calculate_name_number(name)
    grid={i:(birth_num+name_num+i)%9+1 for i in range(1,10)}
    return birth_num,name_num,grid

# ---------------- Remedies Functions ----------------
def get_user_remedies(number,grid_type):
    cursor.execute("SELECT id, category, text FROM remedies WHERE number=? AND grid_type=?",(number,grid_type))
    return cursor.fetchall()

def get_remedies(num,grid_type,status=None):
    text=default_remedies.get(num,"")
    if status: text=f"{status} | Recommended: {text}"
    user_remedies=get_user_remedies(num,grid_type)
    for rid,cat,utext in user_remedies: text+=f"\n[{cat}] {utext}"
    return text

# ---------------- PDF with Logo/Header/Footer ----------------
class PDF(FPDF):
    def header(self):
        if os.path.exists(logo_path):
            try:
                self.image(logo_path,10,8,33)
            except Exception:
                pass
        self.set_font('Arial','B',16)
        self.cell(0,10,'DevineNumbers - Numerology Report',0,1,'C')
        self.set_font('Arial','',12)
        self.cell(0,5,f'Generated on: {datetime.now().strftime("%d-%m-%Y %H:%M")}',0,1,'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial','I',10)
        self.cell(0,10,'Page %s / {nb}' % self.page_no(),0,0,'C')

def generate_pdf(name,dob,loshu_grid,loshu_analysis,birth_num,name_num,vedic_grid,filepath):
    pdf=PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Arial",'',12)
    pdf.cell(0,10,f"Name: {name}",0,1)
    pdf.cell(0,10,f"DOB: {dob}",0,1)
    pdf.set_font("Arial",'B',14)
    pdf.cell(0,10,"Lo Shu Grid Analysis",0,1)
    pdf.set_font("Arial",'',12)
    for num,status in loshu_analysis.items():
        pdf.multi_cell(0,8,f"{num}: {status} | {get_remedies(num,'LoShu',status)}")
    pdf.ln(5)
    pdf.set_font("Arial",'B',14)
    pdf.cell(0,10,"Vedic Grid Analysis",0,1)
    pdf.set_font("Arial",'',12)
    pdf.cell(0,8,f"Birth Number: {birth_num}",0,1)
    pdf.cell(0,8,f"Name Number: {name_num}",0,1)
    pdf.cell(0,8,f"Grid Numbers: {vedic_grid}",0,1)
    for num in range(1,10):
        pdf.multi_cell(0,8,f"Number {num}: {get_remedies(num,'Vedic')}")
    pdf.output(filepath)

# ---------------- Tkinter GUI ----------------
root=tk.Tk()
root.title("DevineNumbers - Numerology Dashboard")
root.geometry("900x950")

# --- Logo ---
def load_logo_image():
    global logo_photo
    try:
        img = Image.open(logo_path)
        img = img.resize((150,150))
        logo_photo = ImageTk.PhotoImage(img)
        logo_label.config(image=logo_photo)
    except Exception:
        pass

logo_label = tk.Label(root)
logo_label.pack(pady=10)
load_logo_image()

tk.Button(root,text="Change Logo",command=lambda: change_logo(),bg="purple",fg="white").pack(pady=5)

# --- Tabs ---
tabControl=ttk.Notebook(root)
tab_dashboard=ttk.Frame(tabControl)
tab_manage=ttk.Frame(tabControl)
tab_daily=ttk.Frame(tabControl)
tabControl.add(tab_dashboard,text="Dashboard")
tabControl.add(tab_manage,text="Manage Remedies")
tabControl.add(tab_daily,text="Daily Insights")
tabControl.pack(expand=1,fill="both")

# --- Dashboard Tab ---
tk.Label(tab_dashboard,text="Full Name:").pack()
entry_name=tk.Entry(tab_dashboard,width=30)
entry_name.pack()
tk.Label(tab_dashboard,text="DOB (DDMMYYYY):").pack()
entry_dob=tk.Entry(tab_dashboard,width=30)
entry_dob.pack()

tk.Button(tab_dashboard,text="Generate Report",bg="green",fg="white",
          command=lambda: generate_report()).pack(pady=10)
text_remedies=tk.Text(tab_dashboard,height=15,width=100)
text_remedies.pack()

# --- Manage Remedies Tab ---
frame_remedy=tk.LabelFrame(tab_manage,text="Add Custom Remedy/Prediction")
frame_remedy.pack(padx=10,pady=10,fill="x")
tk.Label(frame_remedy,text="Number(1-9):").grid(row=0,column=0)
entry_remedy_number=tk.Entry(frame_remedy,width=5)
entry_remedy_number.grid(row=0,column=1)
tk.Label(frame_remedy,text="Grid Type:").grid(row=0,column=2)
var_grid_type=tk.StringVar(value="LoShu")
tk.OptionMenu(frame_remedy,var_grid_type,"LoShu","Vedic").grid(row=0,column=3)
tk.Label(frame_remedy,text="Category:").grid(row=1,column=0)
entry_category=tk.Entry(frame_remedy,width=20)
entry_category.grid(row=1,column=1,columnspan=3)
tk.Label(frame_remedy,text="Remedy / Prediction:").grid(row=2,column=0)
entry_remedy_text=tk.Text(frame_remedy,height=4,width=50)
entry_remedy_text.grid(row=3,column=0,columnspan=4)
tk.Button(frame_remedy,text="Add Remedy",command=lambda: add_remedy(),bg="blue",fg="white").grid(row=4,column=0,columnspan=4,pady=5)

listbox_remedies=tk.Listbox(tab_manage,width=120,height=10)
listbox_remedies.pack()
tk.Button(tab_manage,text="Edit Selected",command=lambda: edit_selected_remedy(),bg="orange").pack(side="left",padx=5)
tk.Button(tab_manage,text="Delete Selected",command=lambda: delete_selected_remedy(),bg="red").pack(side="left",padx=5)

#def update_remedies_list():
#    import sqlite3
#    conn = sqlite3.connect('numerology_remedies.db')
#    cursor = conn.cursor()
#    cursor.execute("SELECT * FROM remedies")
#    remedies = cursor.fetchall()
#    conn.close()
#    print("Remedies reloaded:", remedies)

#update_remedies_list()

# --- Daily Insights Tab ---
tk.Label(tab_daily,text="Your Daily Numerology Insight").pack(pady=10)
text_daily=tk.Text(tab_daily,height=15,width=100)
text_daily.pack()

# ---------------- Functions ----------------
def change_logo():
    global logo_photo, logo_path
    file_path = filedialog.askopenfilename(title="Select Logo", filetypes=[("Image Files","*.png *.jpg *.jpeg")])
    if file_path:
        shutil.copy(file_path, user_logo_path)
        logo_path = user_logo_path
        load_logo_image()
        messagebox.showinfo("Success","Logo updated successfully!")

def daily_numerology():
    dob=entry_dob.get().strip()
    if dob:
        birth_num=calculate_birth_number(dob)
        day_sum=sum([int(x) for x in datetime.today().strftime("%d%m%Y")])
        lucky_num=(birth_num+day_sum)%9 or 9
        lucky_color=default_remedies[lucky_num].split(",")[1]
        text_daily.delete("1.0",tk.END)
        text_daily.insert(tk.END,f"Today's Lucky Number: {lucky_num}\nLucky Color: {lucky_color}")

def add_remedy():
    try: number=int(entry_remedy_number.get())
    except: messagebox.showerror("Error","Enter a valid number"); return
    grid_type=var_grid_type.get()
    category=entry_category.get().strip()
    text=entry_remedy_text.get("1.0",tk.END).strip()
    if not text: messagebox.showerror("Error","Enter remedy text"); return
    cursor.execute("INSERT INTO remedies(number,grid_type,category,text) VALUES(?,?,?,?)",(number,grid_type,category,text))
    conn.commit()
    messagebox.showinfo("Success","Remedy added")
    entry_remedy_text.delete("1.0",tk.END)
    update_remedies_list()

def update_remedies_list():
    listbox_remedies.delete(0,tk.END)
    cursor.execute("SELECT id, number, grid_type, category, text FROM remedies ORDER BY grid_type,number")
    for row in cursor.fetchall():
        listbox_remedies.insert(tk.END,f"ID:{row[0]} | Num:{row[1]} | {row[2]} | {row[3]} | {row[4][:30]}...")

def edit_selected_remedy():
    selection=listbox_remedies.curselection()
    if not selection: return
    idx=listbox_remedies.get(selection[0])
    rid=int(idx.split("|")[0].split(":")[1])
    new_text=simpledialog.askstring("Edit Remedy","Enter new text")
    if new_text: cursor.execute("UPDATE remedies SET text=? WHERE id=?",(new_text,rid)); conn.commit(); update_remedies_list()

def delete_selected_remedy():
    selection=listbox_remedies.curselection()
    if not selection: return
    idx=listbox_remedies.get(selection[0])
    rid=int(idx.split("|")[0].split(":")[1])
    cursor.execute("DELETE FROM remedies WHERE id=?",(rid,)); conn.commit(); update_remedies_list()

def generate_report():
    name=entry_name.get().strip()
    dob=entry_dob.get().strip()
    if not name or not dob: messagebox.showerror("Error","Enter Name and DOB"); return
    loshu_grid=generate_loshu_grid(dob)
    loshu_analysis=analyze_loshu_grid(loshu_grid)
    birth_num,name_num,vedic_grid=generate_vedic_grid(dob,name)
    daily_numerology()
    filepath=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")])
    if filepath: generate_pdf(name,dob,loshu_grid,loshu_analysis,birth_num,name_num,vedic_grid,filepath); messagebox.showinfo("Saved",f"PDF saved to {filepath}")

# ---------------- Backup Function ----------------
def backup_assets():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.path.exists(user_logo_path):
        shutil.copy(user_logo_path, os.path.join(backup_folder, f"user_logo_{timestamp}.png"))
    if os.path.exists(db_path):
        shutil.copy(db_path, os.path.join(backup_folder, f"numerology_remedies_{timestamp}.db"))

# --- Run Backup on Start ---
backup_assets()

# --- On Start ---
daily_numerology()
root.mainloop()
