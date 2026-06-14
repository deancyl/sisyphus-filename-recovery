"""
Sisyphus - GUI for garbled filename recovery
"""
import os, sys, threading, datetime, csv, shutil, hashlib
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import pandas as pd

# Add parent to path for core imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.system_check import get_status, fix_acp
from core.salary_recovery import scan_salary
from core.metadata_recovery import scan_metadata
from core.archive_recovery import scan_archives
from core.text_recovery import scan_textfiles
from core.cluster_recovery import scan_clusterable, get_hash as file_hash
from core.hardcode_recovery import scan_hardcode

# Theme settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SisyphusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sisyphus - File Name Recovery v1.0.0")
        self.geometry("1100x750")
        self.minsize(900, 600)
        
        self.target_dir = ctk.StringVar(value=os.path.expanduser("~\\Downloads"))
        self.preview_data = []
        self.backup_dir = ""
        
        self._build_ui()
        self._check_system()
    
    def _build_ui(self):
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # === Top Bar ===
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(top, text="Target Directory:", font=("", 13)).pack(side="left", padx=(10, 5))
        ctk.CTkEntry(top, textvariable=self.target_dir, width=400).pack(side="left", padx=5)
        ctk.CTkButton(top, text="Browse", width=80, command=self._browse).pack(side="left", padx=5)
        
        self.sys_label = ctk.CTkLabel(top, text="", font=("", 12))
        self.sys_label.pack(side="right", padx=10)
        
        # === Strategy Panel ===
        strat = ctk.CTkFrame(self)
        strat.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(strat, text="Recovery Strategies:", font=("", 13, "bold")).pack(side="left", padx=10)
        
        self.strategies = {}
        options = [
            ("salary", "Excel Salary"),
            ("metadata", "Metadata (PDF/Torrent/Media)"),
            ("archives", "ZIP Interior"),
            ("textfiles", "Text First-Line"),
            ("cluster", "Time Cluster"),
            ("hardcode", "Hardcode + Regex"),
        ]
        for key, label in options:
            var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(strat, text=label, variable=var, width=20).pack(side="left", padx=5)
            self.strategies[key] = var
        
        # === Action Buttons ===
        actions = ctk.CTkFrame(strat)
        actions.pack(side="right", padx=10)
        ctk.CTkButton(actions, text="Scan & Preview", command=self._scan, width=120).pack(side="left", padx=3)
        ctk.CTkButton(actions, text="Execute All", command=self._execute, width=120, 
                      fg_color="#2E7D32", hover_color="#1B5E20").pack(side="left", padx=3)
        
        # === Preview Table ===
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(table_frame, text="Preview (Old Name -> New Name):", 
                     font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Treeview for preview
        columns = ("Old Name", "New Name", "Strategy")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        self.tree.heading("Old Name", text="Old Name")
        self.tree.heading("New Name", text="New Name")
        self.tree.heading("Strategy", text="Strategy")
        self.tree.column("Old Name", width=350)
        self.tree.column("New Name", width=350)
        self.tree.column("Strategy", width=120)
        
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        self.tree.grid(row=1, column=0, sticky="nsew", padx=10)
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew", padx=10)
        
        # === Status Bar ===
        self.status = ctk.CTkLabel(self, text="Ready. Click 'Scan & Preview' to start.", 
                                    font=("", 11), anchor="w")
        self.status.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        
        # === Progress ===
        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.progress.set(0)
    
    def _browse(self):
        path = filedialog.askdirectory(title="Select Target Directory")
        if path:
            self.target_dir.set(path)
    
    def _check_system(self):
        status = get_status()
        color = {"ok": "#4CAF50", "warning": "#FF9800", "error": "#F44336"}
        self.sys_label.configure(
            text=f"System ACP: {status['acp']} - {status['msg']}", 
            text_color=color.get(status['status'], "white"))
        
        if status['status'] == 'warning':
            if messagebox.askyesno("System Encoding Warning",
                                   f"Your system ACP is {status['acp']} (UTF-8).\n"
                                   "This is likely causing garbled filenames.\n\n"
                                   "Fix it to GBK (936)? Requires reboot."):
                ok, msg = fix_acp()
                messagebox.showinfo("Result", msg)
    
    def _set_status(self, msg):
        self.status.configure(text=msg)
        self.update_idletasks()
    
    def _scan(self):
        """Run all enabled strategies and show preview"""
        self._set_status("Scanning...")
        self.tree.delete(*self.tree.get_children())
        self.preview_data = []
        
        directory = self.target_dir.get()
        if not os.path.isdir(directory):
            messagebox.showerror("Error", f"Invalid directory: {directory}")
            return
        
        # Create backup
        self._create_backup(directory)
        
        def scan_worker():
            total = 0
            stages = []
            
            # Phase 2: Salary
            if self.strategies['salary'].get():
                records = scan_salary(directory)
                for old, new in records:
                    self.preview_data.append((old, new, "Salary"))
                total += len(records)
                stages.append(f"Salary: {len(records)}")
            
            # Phase 3: Metadata
            if self.strategies['metadata'].get():
                records = scan_metadata(directory)
                for old, new, strat in records:
                    self.preview_data.append((old, new, strat))
                total += len(records)
                stages.append(f"Metadata: {len(records)}")
            
            # Phase 4-M2: Archives
            if self.strategies['archives'].get():
                records = scan_archives(directory)
                for old, new in records:
                    self.preview_data.append((old, new, "Archive"))
                total += len(records)
                stages.append(f"Archives: {len(records)}")
            
            # Phase 4-M3: Text files
            if self.strategies['textfiles'].get():
                records = scan_textfiles(directory)
                for old, new in records:
                    self.preview_data.append((old, new, "Text"))
                total += len(records)
                stages.append(f"Text: {len(records)}")
            
            # Phase 4-M4: Cluster
            if self.strategies['cluster'].get():
                records = scan_clusterable(directory)
                for old, new, strat in records:
                    self.preview_data.append((old, new, strat))
                total += len(records)
                stages.append(f"Cluster: {len(records)}")
            
            # Phase 5: Hardcode
            if self.strategies['hardcode'].get():
                records = scan_hardcode(directory)
                for old, new, is_dir in records:
                    tag = "DirClean" if is_dir else "Hardcode"
                    self.preview_data.append((old, new, tag))
                total += len(records)
                stages.append(f"Hardcode: {len(records)}")
            
            # Update treeview
            self.after(0, lambda: self._populate_tree())
            self.after(0, lambda: self._set_status(
                f"Scan complete. {total} candidates found. {' | '.join(stages) if stages else 'No matches.'}"))
            self.after(0, lambda: self.progress.set(1))
        
        self.progress.set(0.3)
        threading.Thread(target=scan_worker, daemon=True).start()
    
    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, (old, new, strat) in enumerate(self.preview_data):
            tag = 'even' if i % 2 == 0 else 'odd'
            self.tree.insert('', 'end', values=(old[:80], new[:80], strat), tags=(tag,))
        self.tree.tag_configure('even', background='#2B2B2B')
        self.tree.tag_configure('odd', background='#333333')
    
    def _create_backup(self, directory):
        """Create CSV backup of current filenames"""
        self.backup_dir = os.path.join(directory, "_Sisyphus_Backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"backup_{ts}.csv")
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write("Name,Path,Size\n")
            for item in os.listdir(directory):
                ipath = os.path.join(directory, item)
                size = os.path.getsize(ipath) if os.path.isfile(ipath) else 0
                f.write(f'"{item}","{ipath}",{size}\n')
    
    def _execute(self):
        """Execute renames based on preview"""
        if not self.preview_data:
            messagebox.showwarning("No Data", "Run 'Scan & Preview' first.")
            return
        
        directory = self.target_dir.get()
        trash = os.path.join(directory, "_Trash_Duplicates")
        os.makedirs(trash, exist_ok=True)
        
        self._set_status("Executing...")
        self.progress.set(0)
        
        def exec_worker():
            renamed = 0; deleted = 0; clustered = 0; failed = 0
            log_rows = []
            total = len(self.preview_data)
            
            for i, (old, new, strat) in enumerate(self.preview_data):
                old_path = os.path.join(directory, old)
                if not os.path.exists(old_path):
                    failed += 1; continue
                
                # Handle cluster moves
                if '/' in new or '\\' in new:
                    parts = new.replace('\\', '/').split('/')
                    folder = os.path.join(directory, parts[0])
                    os.makedirs(folder, exist_ok=True)
                    target = os.path.join(folder, parts[1])
                    try:
                        shutil.move(old_path, target)
                        clustered += 1
                        log_rows.append((old, new, "MOVED", strat))
                    except Exception as e:
                        failed += 1
                        log_rows.append((old, new, f"FAIL: {e}", strat))
                else:
                    target = os.path.join(directory, new)
                    if os.path.exists(target):
                        # Hash disambiguation
                        from core.cluster_recovery import resolve_collision
                        action, alt = resolve_collision(old_path, target)
                        if action == 'DELETE':
                            trash_path = os.path.join(trash, old)
                            shutil.move(old_path, trash_path)
                            deleted += 1
                            log_rows.append((old, new, "DELETED_DUP", strat))
                        else:
                            alt_path = os.path.join(directory, alt)
                            os.rename(old_path, alt_path)
                            renamed += 1
                            log_rows.append((old, alt, "RENAMED_COLLISION", strat))
                    else:
                        try:
                            os.rename(old_path, target)
                            renamed += 1
                            log_rows.append((old, new, "RENAMED", strat))
                        except Exception as e:
                            failed += 1
                            log_rows.append((old, new, f"FAIL: {e}", strat))
                
                self.after(0, lambda v=(i+1)/total: self.progress.set(v))
            
            # Save log
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = os.path.join(self.backup_dir, f"execution_{ts}.csv")
            df = pd.DataFrame(log_rows, columns=["OldName","NewName","Action","Strategy"])
            df.to_csv(log_path, index=False, encoding='utf-8-sig')
            
            msg = f"Done! Renamed: {renamed}, Deleted: {deleted}, Clustered: {clustered}, Failed: {failed}"
            self.after(0, lambda: self._set_status(msg))
            self.after(0, lambda: messagebox.showinfo("Complete", msg + f"\nLog: {log_path}"))
        
        threading.Thread(target=exec_worker, daemon=True).start()
    
    def _on_close(self):
        self.destroy()

if __name__ == "__main__":
    app = SisyphusApp()
    app.mainloop()
