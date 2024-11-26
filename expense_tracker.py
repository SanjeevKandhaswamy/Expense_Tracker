import csv
import os
from datetime import datetime
from collections import defaultdict
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# Constants
DATA_FILE = "data/expenses.csv"

# Firebase Initialization
def init_firebase():
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)
    return firestore.client()

# Initialize Local Data File
def init_file():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Category", "Amount", "Description"])

# Add Expense to Local and Firebase
def add_expense(date, category, amount, description, db=None):
    try:
        amount = float(amount)
        with open(DATA_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([date, category, amount, description])
        if db:
            doc_ref = db.collection("expenses").document()
            doc_ref.set({
                "date": date,
                "category": category,
                "amount": amount,
                "description": description
            })
        messagebox.showinfo("Success", "Expense added successfully!")
    except ValueError:
        messagebox.showerror("Error", "Invalid amount. Please enter a valid number.")

# View Expenses
def view_expenses(tree):
    try:
        tree.delete(*tree.get_children())
        with open(DATA_FILE, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                tree.insert("", END, values=(row["Date"], row["Category"], row["Amount"], row["Description"]))
    except FileNotFoundError:
        messagebox.showerror("Error", "No expense data found.")

# Generate Reports
def generate_report():
    try:
        category_totals = defaultdict(float)
        with open(DATA_FILE, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                category_totals[row["Category"]] += float(row["Amount"])
        
        categories = list(category_totals.keys())
        amounts = list(category_totals.values())
        
        # Bar chart
        plt.figure(figsize=(10, 6))
        plt.bar(categories, amounts, color="teal")
        plt.title("Expenses by Category (Bar Chart)", color="white")
        plt.xlabel("Category", color="white")
        plt.ylabel("Amount", color="white")
        plt.gca().set_facecolor("black")
        plt.gcf().set_facecolor("black")
        plt.tick_params(colors="white")
        
        # Pie chart
        plt.figure(figsize=(6, 6))
        plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors[:len(categories)])
        plt.title("Expenses by Category (Pie Chart)", color="white")
        plt.legend(loc="best")
        plt.gca().set_facecolor("black")
        plt.gcf().set_facecolor("black")
        plt.tick_params(colors="white")
        
        plt.show()
    except FileNotFoundError:
        messagebox.showerror("Error", "No expense data found.")

# Export to Excel
def export_to_excel():
    try:
        df = pd.read_csv(DATA_FILE)
        save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if save_path:
            with pd.ExcelWriter(save_path) as writer:
                df.to_excel(writer, index=False, sheet_name="Expenses")
                df.groupby("Category")["Amount"].sum().reset_index().to_excel(writer, index=False, sheet_name="Summary")
            messagebox.showinfo("Success", f"Report exported to {save_path}")
    except FileNotFoundError:
        messagebox.showerror("Error", "No expense data found.")

# Sync Local Data to Firebase
def sync_local_to_firebase(db):
    try:
        with open(DATA_FILE, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                doc_ref = db.collection("expenses").document()
                doc_ref.set({
                    "date": row["Date"],
                    "category": row["Category"],
                    "amount": float(row["Amount"]),
                    "description": row["Description"]
                })
        messagebox.showinfo("Success", "All local data synced to Firebase!")
    except FileNotFoundError:
        messagebox.showerror("Error", "No local data found to sync.")

# Fetch Data from Firebase
def fetch_expenses_from_firebase(db):
    try:
        expenses = db.collection("expenses").stream()
        with open(DATA_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Category", "Amount", "Description"])
            for expense in expenses:
                data = expense.to_dict()
                writer.writerow([data["date"], data["category"], data["amount"], data["description"]])
        messagebox.showinfo("Success", "Data fetched from Firebase and saved locally!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data: {e}")

# Tkinter GUI with ttkbootstrap
def main():
    init_file()
    db = init_firebase()

    # Root Window
    app = ttk.Window(themename="darkly")
    app.title("Expense Tracker with Modern UI")
    app.geometry("900x700")

    # Tabs
    tab_control = ttk.Notebook(app, padding=10)
    add_tab = ttk.Frame(tab_control)
    view_tab = ttk.Frame(tab_control)
    report_tab = ttk.Frame(tab_control)
    tab_control.add(add_tab, text="Add Expense")
    tab_control.add(view_tab, text="View Expenses")
    tab_control.add(report_tab, text="Reports")
    tab_control.pack(expand=1, fill=BOTH)

    # Add Expense Tab
    ttk.Label(add_tab, text="Date (YYYY-MM-DD):", style="primary.TLabel").grid(row=0, column=0, padx=10, pady=10, sticky=W)
    date_entry = ttk.Entry(add_tab, style="info.TEntry")
    date_entry.grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(add_tab, text="Category:", style="primary.TLabel").grid(row=1, column=0, padx=10, pady=10, sticky=W)
    category_entry = ttk.Entry(add_tab, style="info.TEntry")
    category_entry.grid(row=1, column=1, padx=10, pady=10)

    ttk.Label(add_tab, text="Amount:", style="primary.TLabel").grid(row=2, column=0, padx=10, pady=10, sticky=W)
    amount_entry = ttk.Entry(add_tab, style="info.TEntry")
    amount_entry.grid(row=2, column=1, padx=10, pady=10)

    ttk.Label(add_tab, text="Description:", style="primary.TLabel").grid(row=3, column=0, padx=10, pady=10, sticky=W)
    description_entry = ttk.Entry(add_tab, style="info.TEntry")
    description_entry.grid(row=3, column=1, padx=10, pady=10)

    def handle_add():
        add_expense(date_entry.get(), category_entry.get(), amount_entry.get(), description_entry.get(), db)
        date_entry.delete(0, END)
        category_entry.delete(0, END)
        amount_entry.delete(0, END)
        description_entry.delete(0, END)

    ttk.Button(add_tab, text="Add Expense", style="success.TButton", command=handle_add).grid(row=4, column=0, columnspan=2, pady=20)

    # View Expenses Tab
    tree = ttk.Treeview(view_tab, columns=("Date", "Category", "Amount", "Description"), show="headings", height=20, padding=10)
    tree.heading("Date", text="Date")
    tree.heading("Category", text="Category")
    tree.heading("Amount", text="Amount")
    tree.heading("Description", text="Description")
    tree.pack(expand=1, fill=BOTH, padx=10, pady=10)

    ttk.Button(view_tab, text="Refresh", style="info.TButton", command=lambda: view_expenses(tree)).pack(pady=10)

    # Reports Tab
    ttk.Button(report_tab, text="Generate Report", style="success.TButton", command=generate_report).pack(pady=20)
    ttk.Button(report_tab, text="Export to Excel", style="info.TButton", command=export_to_excel).pack(pady=10)
    ttk.Button(report_tab, text="Sync to Cloud", style="primary.TButton", command=lambda: sync_local_to_firebase(db)).pack(pady=10)
    ttk.Button(report_tab, text="Fetch from Cloud", style="primary.TButton", command=lambda: fetch_expenses_from_firebase(db)).pack(pady=10)

    # Run Mainloop
    app.mainloop()

if __name__ == "__main__":
    main()
