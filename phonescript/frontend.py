import tkinter as tk
from tkinter import ttk, messagebox
import json
import sheets
import imessage
import os

FILTER_FILE = "filters.json"


# ---------------- FILTER STORAGE ---------------- #

def load_filters():
    if not os.path.exists(FILTER_FILE):
        return {}
    with open(FILTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("filters", {})


def save_filters(filters):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump({"filters": filters}, f, indent=4)


filters = load_filters()
selected_words = {}


# ---------------- MAIN APP ---------------- #

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mass Text Messenger")
        self.geometry("800x650")

        self.current_sheet_id = None
        self.current_sheet_name = tk.StringVar(value="Current file: None")

        self.build_ui()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=5)

        ttk.Label(top, text="Phone column:").pack(side="left")
        self.phone_column = ttk.Entry(top, width=20)
        self.phone_column.insert(0, "Phone number")
        self.phone_column.pack(side="left", padx=5)

        ttk.Button(top, text="Import Sheet", command=self.open_import_sheet).pack(side="left", padx=5)
        ttk.Button(top, text="Set Filters", command=self.send_message).pack(side="left", padx=5)


        ttk.Label(self, textvariable=self.current_sheet_name, foreground="gray")\
            .pack(anchor="w", padx=10)

        ttk.Label(self, text="Message:").pack(anchor="w", padx=10, pady=(10, 0))
        self.message = tk.Text(self, height=6)
        self.message.pack(fill="x", padx=10)
        
        ttk.Button(top, text="Send Message", command=self.send_message).pack(side="left", padx=5)

        ttk.Label(self, text="Filters:").pack(anchor="w", padx=10, pady=(10, 0))
        self.filter_container = ttk.Frame(self)
        self.filter_container.pack(fill="both", expand=True, padx=10)

        self.refresh_filters()

    # -------- FILTER UI -------- #

    def refresh_filters(self):
        for w in self.filter_container.winfo_children():
            w.destroy()

        if not self.current_sheet_id:
            return

        sheet_filters = filters.get(self.current_sheet_id, {})

        for column, words in sheet_filters.items():
            frame = ttk.LabelFrame(self.filter_container, text=column)
            frame.pack(fill="x", pady=5)

            selected_words.setdefault(column, set())

            for word in words:
                var = tk.BooleanVar(value=word in selected_words[column])
                ttk.Checkbutton(
                    frame,
                    text=word,
                    variable=var,
                    command=lambda c=column, w=word, v=var: self.toggle_word(c, w, v)
                ).pack(side="left", padx=5, pady=5)

    def toggle_word(self, column, word, var):
        if var.get():
            selected_words[column.lower()].add(word.strip().lower())
        else:
            selected_words[column.lower()].discard(word.strip().lower())

    # -------- WINDOWS -------- #

    def open_import_sheet(self):
        ImportSheetWindow(self)
    
    def send_message(self):
        print("sending message")
        print("selected words:")
        print(selected_words)

        auth = sheets.authenticate()
        contacts = sheets.download_sheet_as_csv(auth, self.current_sheet_id, "sheet.csv").lower()
        print("downloaded contacts:")
        print(contacts)
        contacts = sheets.filter_csv(contacts, selected_words)
        print("filtered contacts:")
        print(contacts)

        imessage.send_messages(self.message.get("1.0", "end-1c"), contacts)

    def open_manage_filters(self):
        ManageFiltersWindow(self)



# ---------------- IMPORT SHEET WINDOW ---------------- #

class ImportSheetWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.title("Select Sheet")
        self.geometry("400x300")
        self.grab_set()

        self.auth = sheets.authenticate()
        self.sheets = sheets.list_spreadsheets(self.auth) if self.auth else {}

        ttk.Label(self, text="Select a sheet:").pack(anchor="w", padx=10)
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=5)

        for name in self.sheets:
            self.listbox.insert("end", name)

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10, pady=10)

        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(btns, text="Confirm", command=self.confirm).pack(side="right", padx=5)

    def confirm(self):
        sel = self.listbox.curselection()
        if not sel:
            return

        name = self.listbox.get(sel[0])
        sheet_id = self.sheets[name]

        self.parent.current_sheet_id = sheet_id
        self.parent.current_sheet_name.set(f"Current file: {name}")

        filters.setdefault(sheet_id, {})
        save_filters(filters)

        self.parent.refresh_filters()
        self.destroy()


class ManageFiltersWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.sheet_id = parent.current_sheet_id

        self.title("Manage Filters")
        self.geometry("600x400")
        self.grab_set()

        self.selected_column = tk.StringVar()
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Columns").pack(anchor="w")
        self.column_list = tk.Listbox(left)
        self.column_list.pack(fill="y")
        self.column_list.bind("<<ListboxSelect>>", self.select_column)

        for col in filters[self.sheet_id]:
            self.column_list.insert("end", col)

        ttk.Button(left, text="Add Column", command=self.add_column).pack(fill="x", pady=2)
        ttk.Button(left, text="Delete Column", command=self.delete_column).pack(fill="x", pady=2)

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True, padx=10)

        ttk.Label(right, text="Words").pack(anchor="w")
        self.word_list = tk.Listbox(right)
        self.word_list.pack(fill="both", expand=True)

        self.word_entry = ttk.Entry(right)
        self.word_entry.pack(fill="x", pady=5)

        ttk.Button(right, text="Add Word", command=self.add_word).pack(fill="x")
        ttk.Button(right, text="Delete Word", command=self.delete_word).pack(fill="x")

    def select_column(self, _):
        sel = self.column_list.curselection()
        if not sel:
            return

        col = self.column_list.get(sel[0])
        self.selected_column.set(col)

        self.word_list.delete(0, "end")
        for w in filters[self.sheet_id][col]:
            self.word_list.insert("end", w)

    def add_column(self):
        name = simple_input(self, "New Column", "Column name:")
        if not name:
            return

        filters[self.sheet_id][name] = []
        self.column_list.insert("end", name)
        save_filters(filters)

    def delete_column(self):
        col = self.selected_column.get()
        if not col:
            return

        del filters[self.sheet_id][col]
        save_filters(filters)

        self.column_list.delete(0, "end")
        for c in filters[self.sheet_id]:
            self.column_list.insert("end", c)

        self.word_list.delete(0, "end")

    def add_word(self):
        col = self.selected_column.get()
        word = self.word_entry.get().strip()
        if not col or not word:
            return

        filters[self.sheet_id][col].append(word)
        self.word_list.insert("end", word)
        self.word_entry.delete(0, "end")
        save_filters(filters)

    def delete_word(self):
        col = self.selected_column.get()
        sel = self.word_list.curselection()
        if not col or not sel:
            return

        word = self.word_list.get(sel[0])
        filters[self.sheet_id][col].remove(word)
        self.word_list.delete(sel[0])
        save_filters(filters)


# ---------------- SIMPLE INPUT ---------------- #

def simple_input(parent, title, prompt):
    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry("300x120")
    win.grab_set()

    ttk.Label(win, text=prompt).pack(pady=5)
    entry = ttk.Entry(win)
    entry.pack(fill="x", padx=10)

    value = {"v": None}

    def ok():
        value["v"] = entry.get()
        win.destroy()

    ttk.Button(win, text="OK", command=ok).pack(pady=10)
    
    return value["v"]

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    App().mainloop()
