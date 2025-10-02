import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sqlite3
from PIL import Image, ImageTk
import google.generativeai as genai
import threading
import csv
import time
from datetime import datetime

# --- SettingsManager osztály ---
class SettingsManager:
    """
    Kezeli a beállítások mentését és betöltését JSON fájlból.
    """
    def __init__(self, filename='config.json'):
        self.filename = filename
        self.default_settings = {
            "folders": "",
            "google_api_key": "",
            # Új alapértelmezett beállítás a prompt számára
            "ai_prompt": "Adjon meg egy 10 szóból álló kulcsszó listát, amely leírja a képen látható eseményt "
                         "vagy cselekvést. A választ vesszővel elválasztott listaként adja meg, pl.: 'kulcsszó1, kulcsszó2, ...'",
            "column_widths": {},
            "filter_settings": {
                "file_path_query": "",
                "ai_keywords_query": "",
                "used_date_from_query": "",
                "used_date_to_query": "",
                "date_filter_type": "Nincs",
                "logical_operator": "ÉS",
                "used_filter": "Mind",
                "top_limit": "10"
            }
        }

    def load_settings(self):
        """
        Beolvassa a beállításokat a fájlól.
        """
        settings = {}
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Hiba a beállítások betöltésekor: {e}. Alapértelmezett értékek használata.")
        
        # Gondoskodik róla, hogy az összes kulcs létezzen
        for key, value in self.default_settings.items():
            if key not in settings:
                settings[key] = value
                
        # Gondoskodik róla, hogy az alkulcsok létezzenek
        if "filter_settings" not in settings:
            settings["filter_settings"] = self.default_settings["filter_settings"]
        else:
            for key, value in self.default_settings["filter_settings"].items():
                if key not in settings["filter_settings"]:
                    settings["filter_settings"][key] = value
                        
        return settings

    def save_settings(self, settings):
        """
        Elmenti a beállításokat a fájlba.
        """
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Hiba", f"Nem sikerült a beállításokat elmenteni: {e}")
            return False
# ---

# --- DatabaseManager osztály ---
class DatabaseManager:
    """
    Kezeli a SQLite adatbázissal való interakciót.
    """
    def __init__(self, db_name='app_database.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_table()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            messagebox.showerror("Adatbázis hiba", f"Nem sikerült kapcsolódni az adatbázishoz: {e}")

    def create_table(self):
        if self.cursor:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    file_path TEXT PRIMARY KEY NOT NULL,
                    ai_keywords TEXT,
                    used_date TEXT,
                    used INTEGER DEFAULT 0
                )
            ''')
            self.conn.commit()

    def insert_new_file(self, file_path):
        if self.cursor:
            try:
                self.cursor.execute("INSERT INTO files (file_path, used_date, used) VALUES (?, ?, ?)", (file_path, None, 0))
                self.conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
            except sqlite3.Error as e:
                print(f"Hiba a fájl beszúrásakor ({file_path}): {e}")
                return False

    def fetch_all_files(self):
        try:
            self.cursor.execute("SELECT file_path, ai_keywords, used_date, used FROM files")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Adatbázis hiba", f"Nem sikerült az adatok lekérdezése: {e}")
            return []
            
    def delete_records(self, file_paths):
        if not file_paths:
            return 0
            
        placeholders = ','.join('?' for _ in file_paths)
        sql = f"DELETE FROM files WHERE file_path IN ({placeholders})"
        
        try:
            self.cursor.execute(sql, file_paths)
            self.conn.commit()
            return self.cursor.rowcount
        except sqlite3.Error as e:
            messagebox.showerror("Adatbázis hiba", f"Nem sikerült a rekordok törlése: {e}")
            return 0

    def fetch_files(self, limit=10, filter_queries=None, date_filter=None, logical_operator="AND", order_by="file_path", order_direction="ASC"):
        query = "SELECT file_path, ai_keywords, used_date, used FROM files"
        params = []
        where_clauses = []
        
        if filter_queries:
            for column, search_query in filter_queries.items():
                if search_query is not None:
                    if column == "used":
                        where_clauses.append(f"{column} = ?")
                        params.append(search_query)
                    else:
                        where_clauses.append(f"{column} LIKE ?")
                        params.append(f"%{search_query}%")
        
        if date_filter and date_filter["type"] != "Nincs":
            date_col = "used_date"
            filter_type = date_filter["type"]
            date_from = date_filter["from"]
            date_to = date_filter["to"]
            
            if date_from or date_to:
                date_where_clauses = []
                date_clause_base = f"({date_col} IS NOT NULL AND {date_col} != ''"
                
                if filter_type == "Korábbi, mint" and date_from:
                    date_where_clauses.append(f"{date_clause_base} AND {date_col} < ?)")
                    params.append(date_from)
                elif filter_type == "Későbbi, mint" and date_from:
                    date_where_clauses.append(f"{date_clause_base} AND {date_col} > ?)")
                    params.append(date_from)
                elif filter_type == "Közte":
                    if date_from and date_to:
                        date_where_clauses.append(f"{date_clause_base} AND {date_col} BETWEEN ? AND ?)")
                        params.append(date_from)
                        params.append(date_to)
                    elif date_from:
                        date_where_clauses.append(f"{date_clause_base} AND {date_col} >= ?)")
                        params.append(date_from)
                    elif date_to:
                        date_where_clauses.append(f"{date_clause_base} AND {date_col} <= ?)")
                        params.append(date_to)
            
                if date_where_clauses:
                    where_clauses.append(" AND ".join(date_where_clauses))

        
        if where_clauses:
            operator = " AND " if logical_operator == "AND" else " OR "
            query += " WHERE " + operator.join(where_clauses)
        
        order_clause = f" ORDER BY {order_by} {order_direction}"
        
        query += order_clause + f" LIMIT ?"
        params.append(limit)
        
        try:
            self.cursor.execute(query, tuple(params))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Adatbázis hiba", f"Nem sikerült a lekérdezés: {e} \nLekérdezés: {query} \nParaméterek: {params}")
            return []

    def update_record(self, file_path, column, new_value):
        try:
            # Megjegyzés: A new_value lehet None, ami NULL értéket fog beállítani
            self.cursor.execute(f"UPDATE files SET {column} = ? WHERE file_path = ?", (new_value, file_path))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Adatbázis hiba", f"Hiba az adat frissítésekor: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
# ---

# --- MainApp osztály ---
class MainApp(tk.Tk):
    """
    Fő alkalmazásosztály, ami felépíti a Tkinter GUI-t és kezeli a funkciókat.
    """
    def __init__(self):
        super().__init__()
        self.title("Képfájl-kezelő alkalmazás")
        self.state('zoomed')
        
        try:
            self.iconbitmap('icon.ico')
        except tk.TclError:
            pass # Nincs icon.ico

        self.settings_manager = SettingsManager()
        self.db_manager = DatabaseManager()
        
        self.file_path_query = tk.StringVar(value="")
        self.ai_keywords_query = tk.StringVar(value="")
        self.used_date_from_query = tk.StringVar(value="")
        self.used_date_to_query = tk.StringVar(value="")
        self.date_filter_type = tk.StringVar(value="Nincs")
        
        self.logical_operator = tk.StringVar(value="ÉS")
        self.used_filter_var = tk.StringVar(value="Mind")
        self.top_limit = tk.StringVar(value="10")
        
        self.sort_column = "file_path"
        self.sort_direction = "ASC"
        self.dirty_records = {}
        self.date_format = "%Y.%m.%d"
        
        self.create_widgets()
        
        self.load_settings_into_gui()
        self.load_data_to_table()
        
        self.notebook.select(self.data_frame)


    def create_widgets(self):
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Beállítások")
        
        # --- Beállítások fül ---
        
        # Mappa útvonalak
        folder_label = ttk.Label(self.settings_frame, text="Mappa útvonalak (egyenként új sorba):")
        folder_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.folders_text = tk.Text(self.settings_frame, height=10, wrap="word")
        self.folders_text.pack(fill="both", padx=10, pady=5)
        
        # Google AI kulcs
        api_label = ttk.Label(self.settings_frame, text="Google AI Studio API kulcs:")
        api_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.api_entry = ttk.Entry(self.settings_frame, show='*') # Jelszómezővé tettem a biztonságosabb bevitelhez
        self.api_entry.pack(fill="x", padx=10, pady=5)

        # AI Prompt Sablon (ÚJ)
        prompt_label = ttk.Label(self.settings_frame, text="AI Prompt Sablon (mit kérdezzünk meg a képről):")
        prompt_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.prompt_text_area = tk.Text(self.settings_frame, height=5, wrap="word")
        self.prompt_text_area.pack(fill="x", padx=10, pady=5)

        # Gombok
        button_frame = ttk.Frame(self.settings_frame)
        button_frame.pack(fill="x", pady=10)
        save_button = ttk.Button(button_frame, text="Mentés", command=self.save_settings_from_gui)
        save_button.pack(side="left", padx=10, expand=True)
        refresh_button = ttk.Button(button_frame, text="Frissítés/Betöltés", command=self.load_settings_into_gui)
        refresh_button.pack(side="right", padx=10, expand=True)
        
        # --- Adatok fül ---
        
        self.data_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.data_frame, text="Adatok")

        top_section_frame = ttk.Frame(self.data_frame)
        top_section_frame.pack(fill="x", padx=10, pady=5)
        
        left_controls_frame = ttk.Frame(top_section_frame)
        left_controls_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        scan_button = ttk.Button(left_controls_frame, text="Mappák beolvasása", command=self.scan_folders)
        scan_button.pack(pady=10)

        export_button = ttk.Button(left_controls_frame, text="Teljes DB exportálása CSV-be", command=self.export_to_csv)
        export_button.pack(pady=10)
        
        self.status_text = tk.Text(left_controls_frame, height=10, wrap="word")
        self.status_text.pack(fill="both", expand=True, pady=5)

        self.image_frame = ttk.LabelFrame(top_section_frame, text="Kijelölt kép előnézete")
        self.image_frame.pack(side="right", fill="y")
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(padx=5, pady=5)
        self.current_image = None
        
        # --- Szűrési vezérlők ---
        data_controls_frame = ttk.Frame(self.data_frame)
        data_controls_frame.pack(fill="x", padx=10, pady=5)
        
        # Fájl útvonal & AI kulcsszavak
        ttk.Label(data_controls_frame, text="Szűrés:").pack(side="left", padx=(0, 5))
        ttk.Entry(data_controls_frame, textvariable=self.file_path_query, width=20).pack(side="left", padx=5)
        ttk.Label(data_controls_frame, text="Fájl útvonal").pack(side="left")
        ttk.Entry(data_controls_frame, textvariable=self.ai_keywords_query, width=20).pack(side="left", padx=5)
        ttk.Label(data_controls_frame, text="AI kulcsszavak").pack(side="left")

        # Dátum szűrés
        ttk.Label(data_controls_frame, text="Dátum szűrés:").pack(side="left", padx=(10, 5))
        date_filter_combo = ttk.Combobox(data_controls_frame, textvariable=self.date_filter_type, values=["Nincs", "Korábbi, mint", "Későbbi, mint", "Közte"], state="readonly", width=12)
        date_filter_combo.pack(side="left")
        date_filter_combo.bind("<<ComboboxSelected>>", lambda event: self.load_data_to_table())
        
        ttk.Entry(data_controls_frame, textvariable=self.used_date_from_query, width=12).pack(side="left", padx=5)
        ttk.Label(data_controls_frame, text="tól/től").pack(side="left", padx=(0, 5))
        
        ttk.Entry(data_controls_frame, textvariable=self.used_date_to_query, width=12).pack(side="left", padx=5)
        ttk.Label(data_controls_frame, text="ig").pack(side="left")
        
        # E/V, Felhasználva, Limit
        logical_operator_combo = ttk.Combobox(data_controls_frame, textvariable=self.logical_operator, values=["ÉS", "VAGY"], state="readonly", width=5)
        logical_operator_combo.pack(side="left", padx=10)
        logical_operator_combo.bind("<<ComboboxSelected>>", lambda event: self.load_data_to_table())
        
        ttk.Label(data_controls_frame, text="Felhasználva:").pack(side="left", padx=(10, 5))
        used_options = ttk.Combobox(data_controls_frame, textvariable=self.used_filter_var, values=["Mind", "Igen", "Nem"], state="readonly", width=7)
        used_options.pack(side="left")
        used_options.bind("<<ComboboxSelected>>", lambda event: self.load_data_to_table())
        
        ttk.Label(data_controls_frame, text="Elemek száma:").pack(side="left", padx=(10, 5))
        limit_entry = ttk.Entry(data_controls_frame, textvariable=self.top_limit, width=5)
        limit_entry.pack(side="left", padx=5)

        load_data_button = ttk.Button(data_controls_frame, text="Betöltés", command=self.load_data_to_table)
        load_data_button.pack(side="left", padx=(5, 0))
        
        # Fentebb lévő entry-k "Enter" eseményének bekötése
        for child in data_controls_frame.winfo_children():
            if isinstance(child, ttk.Entry):
                child.bind("<Return>", lambda event: self.load_data_to_table())

        # Tömeges műveletek
        bulk_update_and_save_frame = ttk.Frame(self.data_frame)
        bulk_update_and_save_frame.pack(fill="x", padx=10, pady=5)
        
        set_used_yes_btn = ttk.Button(bulk_update_and_save_frame, text="Kijelöltek beállítása: Igen (Dátummal)", command=lambda: self.set_used_status_bulk("Igen"))
        set_used_yes_btn.pack(side="left", padx=(0, 5), expand=True)
        
        set_used_no_btn = ttk.Button(bulk_update_and_save_frame, text="Kijelöltek beállítása: Nem (Dátum törlése)", command=lambda: self.set_used_status_bulk("Nem"))
        set_used_no_btn.pack(side="left", padx=(5, 0), expand=True)

        self.ai_keyword_button = ttk.Button(bulk_update_and_save_frame, text="AI kulcsszavak feltöltése", command=self.start_ai_keyword_generation)
        self.ai_keyword_button.pack(side="left", padx=(10, 5), expand=True)
        
        delete_button = ttk.Button(bulk_update_and_save_frame, text="Kijelöltek törlése", command=self.delete_selected_records)
        delete_button.pack(side="left", padx=10, expand=True)

        self.save_changes_button = ttk.Button(bulk_update_and_save_frame, text="Változtatások mentése", command=self.save_changes, state="disabled")
        self.save_changes_button.pack(side="right", padx=(10, 0))

        # Táblázat (Treeview)
        columns = ("file_path", "ai_keywords", "used_date", "used")
        self.tree = ttk.Treeview(self.data_frame, columns=columns, show="headings", selectmode='extended')
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree.heading("file_path", text="Fájl útvonal", command=lambda: self.handle_sort_column("file_path"))
        self.tree.heading("ai_keywords", text="AI kulcsszavak", command=lambda: self.handle_sort_column("ai_keywords"))
        self.tree.heading("used_date", text="Felhasználás dátuma", command=lambda: self.handle_sort_column("used_date"))
        self.tree.heading("used", text="Felhasználva", command=lambda: self.handle_sort_column("used"))
        
        self.tree.column("file_path", width=300)
        self.tree.column("ai_keywords", width=250)
        self.tree.column("used_date", width=150, anchor=tk.CENTER)
        self.tree.column("used", width=80, anchor=tk.CENTER)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_settings_into_gui(self):
        settings = self.settings_manager.load_settings()
        
        self.folders_text.delete("1.0", tk.END)
        self.folders_text.insert(tk.END, settings.get("folders", ""))
        self.api_entry.delete(0, tk.END)
        self.api_entry.insert(0, settings.get("google_api_key", ""))
        
        # ÚJ: Prompt betöltése
        self.prompt_text_area.delete("1.0", tk.END)
        self.prompt_text_area.insert(tk.END, settings.get("ai_prompt", self.settings_manager.default_settings["ai_prompt"]))
        
        if "column_widths" in settings:
            for col_name, width in settings["column_widths"].items():
                try:
                    self.tree.column(col_name, width=width)
                except tk.TclError:
                    continue
        
        filter_settings = settings.get("filter_settings", self.settings_manager.default_settings["filter_settings"])
        self.file_path_query.set(filter_settings.get("file_path_query", ""))
        self.ai_keywords_query.set(filter_settings.get("ai_keywords_query", ""))
        self.used_date_from_query.set(filter_settings.get("used_date_from_query", ""))
        self.used_date_to_query.set(filter_settings.get("used_date_to_query", ""))
        self.date_filter_type.set(filter_settings.get("date_filter_type", "Nincs"))
        self.logical_operator.set(filter_settings.get("logical_operator", "ÉS"))
        self.used_filter_var.set(filter_settings.get("used_filter", "Mind"))
        self.top_limit.set(filter_settings.get("top_limit", "10"))
        
        print("Beállítások betöltve.")

    def save_settings_from_gui(self):
        settings = {
            "folders": self.folders_text.get("1.0", tk.END).strip(),
            "google_api_key": self.api_entry.get().strip(),
            "ai_prompt": self.prompt_text_area.get("1.0", tk.END).strip(), # ÚJ: Prompt mentése
            "column_widths": {
                "file_path": self.tree.column("file_path", "width"),
                "ai_keywords": self.tree.column("ai_keywords", "width"),
                "used_date": self.tree.column("used_date", "width"),
                "used": self.tree.column("used", "width"),
            },
            "filter_settings": {
                "file_path_query": self.file_path_query.get(),
                "ai_keywords_query": self.ai_keywords_query.get(),
                "used_date_from_query": self.used_date_from_query.get(),
                "used_date_to_query": self.used_date_to_query.get(),
                "date_filter_type": self.date_filter_type.get(),
                
                "logical_operator": self.logical_operator.get(),
                "used_filter": self.used_filter_var.get(),
                "top_limit": self.top_limit.get()
            }
        }
        if self.settings_manager.save_settings(settings):
            messagebox.showinfo("Siker", "A beállítások sikeresen elmentve!")
            print("Beállítások elmentve.")

    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV fájlok", "*.csv"), ("Minden fájl", "*.*")],
            title="Adatbázis exportálása CSV-be"
        )
        if not file_path:
            return

        all_data = self.db_manager.fetch_all_files()
        
        if not all_data:
            messagebox.showinfo("Nincs adat", "Az adatbázis üres, nincs mit exportálni.")
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                headers = ["file_path", "ai_keywords", "used_date", "used"]
                writer.writerow(headers)
                
                writer.writerows(all_data)

            messagebox.showinfo("Siker", f"Az adatok sikeresen exportálva ide: {file_path}")
        except Exception as e:
            messagebox.showerror("Hiba", f"Nem sikerült az exportálás: {e}")

    def scan_folders(self):
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, "Mappák beolvasása elindult...\n")
        
        settings = self.settings_manager.load_settings()
        folders_str = settings.get("folders", "")
        folders = [f.strip() for f in folders_str.split('\n') if f.strip()]
        
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')
        
        total_new_files = 0
        
        for folder_path in folders:
            if not os.path.isdir(folder_path):
                self.status_text.insert(tk.END, f"Hiba: A mappa nem létezik: {folder_path}\n")
                continue
            
            self.status_text.insert(tk.END, f"Mappa beolvasása: {folder_path}\n")
            
            try:
                for file_name in os.listdir(folder_path):
                    if file_name.lower().endswith(image_extensions):
                        full_path = os.path.join(folder_path, file_name)
                        if self.db_manager.insert_new_file(full_path):
                            self.status_text.insert(tk.END, f"  Új fájl hozzáadva: {file_name}\n")
                            total_new_files += 1
            except Exception as e:
                self.status_text.insert(tk.END, f"Hiba a mappa beolvasásakor ({folder_path}): {e}\n")
        
        self.status_text.insert(tk.END, f"\nBeolvasás befejezve. Újonnan hozzáadott fájlok száma: {total_new_files}\n")
        self.load_data_to_table()

    def delete_selected_records(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Nincs kijelölés", "Kérlek, jelölj ki legalább egy sort a törléshez.")
            return

        response = messagebox.askyesno("Törlés megerősítése", f"Biztosan törölni szeretnél {len(selected_items)} rekordot az adatbázisból?")
        if response:
            file_paths_to_delete = [self.tree.item(item, 'values')[0] for item in selected_items]
            
            deleted_count = self.db_manager.delete_records(file_paths_to_delete)
            
            if deleted_count > 0:
                self.status_text.insert(tk.END, f"{deleted_count} rekord sikeresen törölve.\n")
                self.load_data_to_table()
            else:
                self.status_text.insert(tk.END, "Hiba a rekordok törlése során.\n")


    def load_data_to_table(self):
        self.clear_table()
        
        # Limit ellenőrzése
        try:
            limit_str = self.top_limit.get().strip()
            limit = int(limit_str) if limit_str else 10
        except ValueError:
            messagebox.showerror("Hiba", "Az 'Elemek száma' mezőbe egész számot kell írni.")
            return
            
        # Dátum formátum ellenőrzése
        date_from_str = self.used_date_from_query.get().strip()
        date_to_str = self.used_date_to_query.get().strip()
        
        if date_from_str and self.date_filter_type.get() != "Nincs":
            try:
                datetime.strptime(date_from_str, self.date_format)
            except ValueError:
                messagebox.showerror("Hiba", f"Érvénytelen dátum formátum ('{date_from_str}'). Használd ezt: YYYY.MM.DD")
                return
        
        if date_to_str and self.date_filter_type.get() != "Nincs":
            try:
                datetime.strptime(date_to_str, self.date_format)
            except ValueError:
                messagebox.showerror("Hiba", f"Érvénytelen dátum formátum ('{date_to_str}'). Használd ezt: YYYY.MM.DD")
                return

        filter_queries = {}
        if self.file_path_query.get().strip():
            filter_queries["file_path"] = self.file_path_query.get().strip()
        if self.ai_keywords_query.get().strip():
            filter_queries["ai_keywords"] = self.ai_keywords_query.get().strip()

        logical_operator_str = "AND" if self.logical_operator.get() == "ÉS" else "OR"
        
        used_filter_text = self.used_filter_var.get()
        used_filter_value = None
        if used_filter_text == "Igen":
            used_filter_value = 1
        elif used_filter_text == "Nem":
            used_filter_value = 0
            
        if used_filter_value is not None:
             filter_queries["used"] = used_filter_value
             
        # Dátumszűrő összeállítása
        date_filter_settings = {
            "type": self.date_filter_type.get(),
            "from": date_from_str,
            "to": date_to_str
        }

        files = self.db_manager.fetch_files(
            limit=limit,
            filter_queries=filter_queries,
            date_filter=date_filter_settings,
            logical_operator=logical_operator_str,
            order_by=self.sort_column,
            order_direction=self.sort_direction
        )
        
        for item in files:
            used_status = "Igen" if item[3] == 1 else "Nem"
            self.tree.insert("", "end", values=(item[0], item[1], item[2] if item[2] is not None else "", used_status))

        self.dirty_records = {}
        self.save_changes_button.config(state="disabled")
        print(f"Adatok betöltve a táblázatba. Összesen {len(files)} elem.")
        self.display_image(None)

    def handle_sort_column(self, column_name):
        if self.sort_column == column_name:
            self.sort_direction = "DESC" if self.sort_direction == "ASC" else "ASC"
        else:
            self.sort_column = column_name
            self.sort_direction = "ASC"

        self.load_data_to_table()

    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item:
            return
        
        # A 'used' oszlopban a dupla kattintás átkapcsolja az állapotot
        if column == "#4":
            self.toggle_used_status_single(item)
            return
            
        # Engedélyezett szerkesztés az AI kulcsszavak és a dátum mezőkben
        if column not in ["#2", "#3"]:
            return

        x, y, width, height = self.tree.bbox(item, column)
        
        self.entry = ttk.Entry(self.tree)
        self.entry.place(x=x, y=y, width=width, height=height)
        
        current_value = self.tree.item(item, 'values')[int(column[1:])-1]
        self.entry.insert(0, current_value)
        self.entry.focus()

        self.entry.bind("<Return>", lambda e: self.on_edit_finish(item, column, self.entry.get()))
        self.entry.bind("<FocusOut>", lambda e: self.entry.destroy())

    def on_edit_finish(self, item, column, new_value):
        if hasattr(self, 'entry') and self.entry:
            self.entry.destroy()
        
        old_values = self.tree.item(item, 'values')
        new_values = list(old_values)
        
        col_index = int(column[1:]) - 1
        col_name = self.tree.heading(column)['text']
        file_path = old_values[0]
        
        # Dátum validáció
        if col_name == "Felhasználás dátuma" and new_value.strip():
            try:
                datetime.strptime(new_value.strip(), self.date_format)
            except ValueError:
                messagebox.showerror("Hiba", f"Érvénytelen dátum formátum: '{new_value}'. Használd ezt: YYYY.MM.DD (pl. 2025.10.02)")
                return
        
        if new_values[col_index] != new_value.strip():
            new_values[col_index] = new_value.strip()
            self.tree.item(item, values=tuple(new_values))
            
            db_key = "used_date" if col_name == "Felhasználás dátuma" else "ai_keywords"

            if file_path not in self.dirty_records:
                self.dirty_records[file_path] = {}
                
            final_value = new_values[col_index] if new_values[col_index] else None
            self.dirty_records[file_path][db_key] = final_value

            self.save_changes_button.config(state="normal")
            print(f"Módosítás a memóriában: {self.dirty_records}")

    def toggle_used_status_single(self, item):
        old_values = self.tree.item(item, 'values')
        current_used_status = old_values[3]
        
        new_used_status = "Igen" if current_used_status == "Nem" else "Nem"
        new_value_db = 1 if new_used_status == "Igen" else 0
        
        # Ha Igen, beállítja a mai dátumot, ha Nem, törli
        new_date = datetime.now().strftime(self.date_format) if new_value_db == 1 else None
        new_date_display = new_date if new_date else ""
        
        new_values = list(old_values)
        new_values[3] = new_used_status
        new_values[2] = new_date_display
        self.tree.item(item, values=tuple(new_values))

        file_path = old_values[0]
        if file_path not in self.dirty_records:
            self.dirty_records[file_path] = {}
            
        self.dirty_records[file_path]["used"] = new_value_db
        self.dirty_records[file_path]["used_date"] = new_date
        
        self.save_changes_button.config(state="normal")

    def set_used_status_bulk(self, status):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Nincs kijelölés", "Kérlek, jelölj ki legalább egy sort a táblázatban.")
            return

        new_used_status = "Igen" if status == "Igen" else "Nem"
        new_value_db = 1 if status == "Igen" else 0
        new_date = datetime.now().strftime(self.date_format) if new_value_db == 1 else None
        new_date_display = new_date if new_date else ""

        for item in selected_items:
            old_values = self.tree.item(item, 'values')
            file_path = old_values[0]
            
            if file_path not in self.dirty_records:
                self.dirty_records[file_path] = {}
            
            self.dirty_records[file_path]["used"] = new_value_db
            self.dirty_records[file_path]["used_date"] = new_date
            
            new_values = list(old_values)
            new_values[3] = new_used_status
            new_values[2] = new_date_display
            self.tree.item(item, values=tuple(new_values))

        self.save_changes_button.config(state="normal")
        messagebox.showinfo("Kijelölés frissítve", f"{len(selected_items)} sor 'Felhasználva' állapota frissítve a memóriában.")
        
    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            item = selected_items[0]
            file_path = self.tree.item(item, 'values')[0]
            self.display_image(file_path)
        else:
            self.display_image(None)

    def display_image(self, image_path):
        if image_path and os.path.exists(image_path):
            try:
                original_image = Image.open(image_path)
                max_size = (250, 250)
                original_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                self.current_image = ImageTk.PhotoImage(original_image)
                self.image_label.config(image=self.current_image)
                self.image_label.image = self.current_image
            except Exception as e:
                self.image_label.config(image="", text="Hiba a kép betöltésekor")
                self.current_image = None
                print(f"Hiba a kép betöltésekor ({image_path}): {e}")
        else:
            self.image_label.config(image="", text="Nincs kép kiválasztva / nem található")
            self.current_image = None

    def start_ai_keyword_generation(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Nincs kijelölés", "Kérlek, jelölj ki legalább egy sort a táblázatban a kulcsszavak feltöltéséhez.")
            return

        settings = self.settings_manager.load_settings()
        api_key = settings.get("google_api_key")

        if not api_key:
            messagebox.showerror("Hiba", "Kérlek, állítsd be a **Google AI kulcsot** a 'Beállítások' lapon.")
            return
        
        if not settings.get("ai_prompt").strip():
             messagebox.showerror("Hiba", "Kérlek, állítsd be az **AI Prompt Sablont** a 'Beállítások' lapon.")
             return

        self.ai_keyword_button.config(state="disabled")
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, "AI kulcsszavak generálása elindult...\n")
        
        # Az AI prompt átadása a szálnak
        ai_prompt = settings.get("ai_prompt")
        
        ai_thread = threading.Thread(target=self.generate_and_save_ai_keywords, args=(selected_items, api_key, ai_prompt))
        ai_thread.daemon = True
        ai_thread.start()

    def generate_and_save_ai_keywords(self, selected_items, api_key, ai_prompt):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            self.after(0, lambda: self.status_text.insert(tk.END, f"Hiba az AI inicializálása során: {e}\n"))
            self.after(0, lambda: self.ai_keyword_button.config(state="normal"))
            return

        for item in selected_items:
            old_values = self.tree.item(item, 'values')
            file_path = old_values[0]

            if not os.path.exists(file_path):
                self.after(0, lambda p=file_path: self.status_text.insert(tk.END, f"Fájl nem található: {p}. Átugrás.\n"))
                continue

            try:
                # Kép betöltése bájtokba
                image = Image.open(file_path)
                
                # A Gemini API a PIL Image objektumot is fogadja, ami sokkal megbízhatóbb, mint a bájtok manuális kezelése
                response = model.generate_content([ai_prompt, image])
                
                ai_keywords = response.text.strip()
                self.after(0, lambda f=os.path.basename(file_path): self.status_text.insert(tk.END, f"Kulcsszavak generálva ehhez: {f}\n"))
                
                if file_path not in self.dirty_records:
                    self.dirty_records[file_path] = {}
                self.dirty_records[file_path]["ai_keywords"] = ai_keywords
                
                self.after(0, lambda p=file_path, k=ai_keywords: self.update_treeview_ai_keywords(p, k))

            except Exception as e:
                self.after(0, lambda p=file_path, err=e: self.status_text.insert(tk.END, f"Hiba az AI kulcsszavak generálása során ehhez a fájlhoz: {os.path.basename(p)}: {err}\n"))
                
            time.sleep(1.1) # Megjegyzés: A rate-limit elkerülése érdekében

        self.after(0, lambda: self.status_text.insert(tk.END, "AI kulcsszavak generálása befejeződött.\n"))
        self.after(0, lambda: self.ai_keyword_button.config(state="normal"))

    def update_treeview_ai_keywords(self, file_path, keywords):
        for item in self.tree.get_children():
            if self.tree.item(item, 'values')[0] == file_path:
                old_values = self.tree.item(item, 'values')
                new_values = list(old_values)
                new_values[1] = keywords
                self.tree.item(item, values=tuple(new_values))
                self.save_changes_button.config(state="normal")
                break

    def save_changes(self):
        if not self.dirty_records:
            messagebox.showinfo("Nincs módosítás", "Nincs elmenthető változtatás.")
            return

        # Változtatások mentése az adatbázisba
        success_count = 0
        for file_path, changes in self.dirty_records.items():
            for db_column, new_value in changes.items():
                if self.db_manager.update_record(file_path, db_column, new_value):
                    success_count += 1
        
        messagebox.showinfo("Siker", f"{len(self.dirty_records)} rekord sikeresen elmentve!")
        self.dirty_records = {}
        self.save_changes_button.config(state="disabled")
    
    def on_close(self):
        # A beállítások mentése az alkalmazás bezárásakor
        self.save_settings_from_gui()
        self.db_manager.close()
        self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()