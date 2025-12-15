import tkinter as tk
from ui.ui import FinanceDashboard
from util.util import ensure_data_dirs

def main():
    ensure_data_dirs()
    root = tk.Tk()
    root.title("Finance Dashboard")
    root.geometry("1000x700")  # starting window
    FinanceDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
