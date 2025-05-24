import tkinter as tk
from ui.app import CompensationCalculator
from database.db_manager import DatabaseManager # Added import

def main():
    # Initialize database and tables
    # The DatabaseManager's __init__ method calls init_database()
    db_manager = DatabaseManager() 

    root = tk.Tk()
    app = CompensationCalculator(root, db_manager) # Pass db_manager
    # Centering the window, similar to the original app.py's main()
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) / 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) / 2
    root.geometry("+%d+%d" % (x, y-30)) # yを少し上に (as in original)
    root.mainloop()

if __name__ == "__main__":
    main()
