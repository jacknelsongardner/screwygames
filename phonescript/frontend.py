import customtkinter as ctk
import tkinter as tk
import json
import sheets
import imessage
import os

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

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

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mass Text Messenger")
        self.geometry("900x700")

        self.current_sheet_id = None
        self.current_sheet_name = tk.StringVar(value="Current file: None")

        self.build_ui()

    def build_ui(self):
        # ---------- Top Bar ----------
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(top, text="Phone column:").pack(side="left")
        self.phone_column = ctk.CTkEntry(top, width=180)
        self.phone_column.insert(0, "Phone number")
        self.phone_column.pack(side="left", padx=8)

        ctk.CTkButton(top, text="Import Sheet", command=self.open_import_sheet).pack(side="left", padx=5)
        ctk.CTkButton(top, text="Manage Filters", command=self.open_manage_filters).pack(side="left", padx=5)
        ctk.CTkButton(top, text="Send Message", command=self.send_message).pack(side="right")

        # ---------- Current Sheet ----------
        ctk.CTkLabel(
            self,
            textvariable=self.current_sheet_name,
            text_color="gray"
        ).pack(anchor="w", padx=20)

        # ---------- Message ----------
        ctk.CTkLabel(self, text="Message").pack(anchor="w", padx=20, pady=(15, 0))
        self.message = ctk.CTkTextbox(self, height=120)
        self.message.pack(fill="x", padx=20)

        # ---------- Filters ----------
        ctk.CTkLabel(self, text="Filters").pack(anchor="w", padx=20, pady=(15, 0))
        self.filter_container = ctk.CTkScrollableFrame(self)
        self.filter_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.refresh_filters()

    # ---------- FILTER UI ----------

    def refresh_filters(self):
        for w in self.filter_container.winfo_children():
            w.destroy()

        if not self.current_sheet_id:
            return

        sheet_filters = filters.get(self.current_sheet_id, {})

        for column, words in sheet_filters.items():
            frame = ctk.CTkFrame(self.filter_container)
            frame.pack(fill="x", pady=6)

            ctk.CTkLabel(frame, text=column, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5, 0))

            selected_words.setdefault(column.lower(), set())

            word_row = ctk.CTkFrame(frame)
            word_row.pack(fill="x", padx=10, pady=5)

            for word in words:
                var = tk.BooleanVar(value=word in selected_words[column.lower()])
                cb = ctk.CTkCheckBox(
                    word_row,
                    text=word,
                    variable=var,
                    command=lambda c=column, w=word, v=var: self.toggle_word(c, w, v)
                )
                cb.pack(side="left", padx=6)

    def toggle_word(self, column, word, var):
        key = column.lower()
        if var.get():
            selected_words.setdefault(key, set()).add(word.lower())
        else:
            selected_words.setdefault(key, set()).discard(word.lower())

    # ---------- ACTIONS ----------

    def open_import_sheet(self):
        ImportSheetWindow(self)

    def open_manage_filters(self):
        if not self.current_sheet_id:
            return
        ManageFiltersWindow(self)

    def send_message(self):
        auth = sheets.authenticate()
        contacts = sheets.download_sheet_as_csv(auth, self.current_sheet_id, "sheet.csv").lower()
        contacts = sheets.filter_csv(contacts, selected_words)
        imessage.send_messages(self.message.get("1.0", "end-1c"), contacts)


# ---------------- IMPORT SHEET WINDOW ---------------- #

class ImportSheetWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Select Sheet")
        self.geometry("450x350")
        self.grab_set()

        self.auth = sheets.authenticate()
        self.sheets = sheets.list_spreadsheets(self.auth) if self.auth else {}

        ctk.CTkLabel(self, text="Select a sheet").pack(anchor="w", padx=15, pady=10)

        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill="both", expand=True, padx=15)

        for name in self.sheets:
            self.listbox.insert("end", name)

        btns = ctk.CTkFrame(self)
        btns.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(btns, text="Cancel", command=self.destroy).pack(side="right")
        ctk.CTkButton(btns, text="Confirm", command=self.confirm).pack(side="right", padx=8)

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


# ---------------- MANAGE FILTERS ---------------- #

class ManageFiltersWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.sheet_id = parent.current_sheet_id
        self.title("Manage Filters")
        self.geometry("700x450")
        self.grab_set()

        self.selected_column = tk.StringVar()
        self.build_ui()

    def build_ui(self):
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # ---------- Left ----------
        left = ctk.CTkFrame(main, width=200)
        left.pack(side="left", fill="y")

        ctk.CTkLabel(left, text="Columns").pack(pady=5)
        self.column_list = tk.Listbox(left)
        self.column_list.pack(fill="y", expand=True, padx=5)
        self.column_list.bind("<<ListboxSelect>>", self.select_column)

        for col in filters[self.sheet_id]:
            self.column_list.insert("end", col)

        ctk.CTkButton(left, text="Add Column", command=self.add_column).pack(fill="x", pady=4)
        ctk.CTkButton(left, text="Delete Column", command=self.delete_column).pack(fill="x", pady=4)

        # ---------- Right ----------
        right = ctk.CTkFrame(main)
        right.pack(side="left", fill="both", expand=True, padx=15)

        ctk.CTkLabel(right, text="Words").pack(anchor="w")
        self.word_list = tk.Listbox(right)
        self.word_list.pack(fill="both", expand=True)

        self.word_entry = ctk.CTkEntry(right)
        self.word_entry.pack(fill="x", pady=8)

        ctk.CTkButton(right, text="Add Word", command=self.add_word).pack(fill="x")
        ctk.CTkButton(right, text="Delete Word", command=self.delete_word).pack(fill="x", pady=5)

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
    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.geometry("320x140")
    win.grab_set()

    ctk.CTkLabel(win, text=prompt).pack(pady=10)
    entry = ctk.CTkEntry(win)
    entry.pack(fill="x", padx=20)

    value = {"v": None}

    def ok():
        value["v"] = entry.get()
        win.destroy()

    ctk.CTkButton(win, text="OK", command=ok).pack(pady=10)
    return value["v"]


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    App().mainloop()
