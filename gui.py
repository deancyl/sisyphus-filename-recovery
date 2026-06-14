"""
Sisyphus v1.0.1 - Garbled Filename Recovery GUI (i18n: zh/en)
Pure tkinter implementation
"""
import os, sys, threading, datetime, csv, shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.i18n import i18n as _i18n

# Lazy core imports
_core = False
def _load_core():
    global _core, scan_salary, scan_metadata, scan_archives, scan_textfiles, scan_clusterable, scan_hardcode, get_status, fix_acp, get_hash, resolve_collision
    if _core: return
    from core.salary_recovery import scan_salary
    from core.metadata_recovery import scan_metadata
    from core.archive_recovery import scan_archives
    from core.text_recovery import scan_textfiles
    from core.cluster_recovery import scan_clusterable, get_hash, resolve_collision
    from core.hardcode_recovery import scan_hardcode
    from core.system_check import get_status, fix_acp
    _core = True


class SisyphusApp:
    def __init__(self):
        self.root = tk.Tk()
        self._ = _i18n.get  # shorthand
        self.root.title(self._("title"))
        self.root.geometry("1100x700")
        self.root.minsize(800, 500)
        
        self.target_dir = tk.StringVar(value=os.path.expanduser("~\\Downloads"))
        self.preview_data = []
        self.backup_dir = ""
        self.running = False
        self.strat_vars = {}
        
        self._build_ui()
        self._check_system()
    
    def _build_ui(self):
        r = self.root
        r.grid_columnconfigure(0, weight=1)
        r.grid_rowconfigure(3, weight=1)
        
        # === Row 0: Directory + Language ===
        top = ttk.Frame(r, padding=5)
        top.grid(row=0, column=0, sticky="ew")
        
        ttk.Label(top, text=self._("target_label")).pack(side="left", padx=(5,2))
        ttk.Entry(top, textvariable=self.target_dir, width=55).pack(side="left", padx=2)
        ttk.Button(top, text=self._("browse"), command=self._browse).pack(side="left", padx=2)
        
        # Language toggle
        lang_frame = ttk.Frame(top)
        lang_frame.pack(side="right", padx=10)
        ttk.Label(lang_frame, text=self._("lang_label")).pack(side="left")
        self.lang_var = tk.StringVar(value=_i18n.lang)
        ttk.Combobox(lang_frame, textvariable=self.lang_var, values=_i18n.get_all_langs(),
                      width=4, state="readonly").pack(side="left", padx=2)
        self.lang_var.trace("w", self._on_lang_change)
        
        # ACP status
        self.sys_label = ttk.Label(top, text="", foreground="gray")
        self.sys_label.pack(side="right", padx=10)
        
        # === Row 1: Strategies ===
        sf = ttk.LabelFrame(r, text=self._("strategies_label"), padding=5)
        sf.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        strategies = [
            ("salary", "strategy_salary"),
            ("metadata", "strategy_metadata"),
            ("archives", "strategy_archives"),
            ("textfiles", "strategy_textfiles"),
            ("cluster", "strategy_cluster"),
            ("hardcode", "strategy_hardcode"),
        ]
        for key, label_key in strategies:
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(sf, text=self._(label_key), variable=var).pack(side="left", padx=8)
            self.strat_vars[key] = var
        
        # === Row 2: Buttons ===
        bf = ttk.Frame(r, padding=5)
        bf.grid(row=2, column=0, sticky="ew")
        
        self.btn_scan = ttk.Button(bf, text=self._("btn_scan"), command=self._scan, width=18)
        self.btn_scan.pack(side="left", padx=5)
        self.btn_exec = ttk.Button(bf, text=self._("btn_execute"), command=self._execute, width=18, state="disabled")
        self.btn_exec.pack(side="left", padx=5)
        ttk.Button(bf, text=self._("btn_export"), command=self._export, width=18).pack(side="left", padx=5)
        ttk.Button(bf, text=self._("btn_clear"), command=self._clear, width=18).pack(side="left", padx=5)
        
        self.count_lbl = ttk.Label(bf, text="")
        self.count_lbl.pack(side="right", padx=10)
        
        # === Row 3: Treeview ===
        tf = ttk.Frame(r)
        tf.grid(row=3, column=0, sticky="nsew", padx=5, pady=2)
        tf.grid_columnconfigure(0, weight=1)
        tf.grid_rowconfigure(0, weight=1)
        
        cols = ("#", "Old Name", "New Name", "Strategy")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="extended", height=18)
        self.tree.heading("#", text=self._("col_num"))
        self.tree.heading("Old Name", text=self._("col_old"))
        self.tree.heading("New Name", text=self._("col_new"))
        self.tree.heading("Strategy", text=self._("col_strategy"))
        self.tree.column("#", width=40, anchor="center")
        self.tree.column("Old Name", width=350)
        self.tree.column("New Name", width=350)
        self.tree.column("Strategy", width=140)
        
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        self.tree.tag_configure("even", background="#f0f0f0")
        self.tree.tag_configure("odd", background="white")
        
        # === Row 4: Status + Progress ===
        sf2 = ttk.Frame(r, padding=3)
        sf2.grid(row=4, column=0, sticky="ew")
        
        self.status_lbl = ttk.Label(sf2, text=self._("status_ready"), relief="sunken", anchor="w", padding=2)
        self.status_lbl.pack(side="top", fill="x")
        self.progress = ttk.Progressbar(sf2, mode="determinate")
        self.progress.pack(side="bottom", fill="x", pady=2)
    
    def _on_lang_change(self, *args):
        new_lang = self.lang_var.get()
        if new_lang != _i18n.lang:
            _i18n.set_lang(new_lang)
            self._refresh_ui_texts()
    
    def _refresh_ui_texts(self):
        """Rebuild all translatable UI text"""
        self.root.title(self._("title"))
        # Too invasive to rebuild - just ask restart for now
        messagebox.showinfo("Language", "Restart the application for language change to take full effect.")
    
    def _set_status(self, msg):
        self.status_lbl.configure(text=msg)
        self.root.update_idletasks()
    
    def _browse(self):
        path = filedialog.askdirectory(title="Target Directory")
        if path: self.target_dir.set(path)
    
    def _check_system(self):
        try:
            _load_core()
            s = get_status()
            colors = {"ok": "green", "warning": "orange", "error": "red"}
            tag = self._("acp_ok") if s["status"]=="ok" else (self._("acp_warn") if s["status"]=="warning" else s["msg"])
            self.sys_label.configure(
                text=f"ACP: {s['acp']} - {tag}",
                foreground=colors.get(s['status'], "black"))
        except Exception as e:
            self.sys_label.configure(text=f"ACP: ? - {e}", foreground="red")
    
    # ======== Scan ========
    def _scan(self):
        if self.running: return
        dir_ = self.target_dir.get()
        if not os.path.isdir(dir_):
            messagebox.showerror("Error", self._("err_invalid_dir") + "\n" + dir_)
            return
        
        self.running = True
        self._set_status(self._("status_loading"))
        self.btn_scan.configure(state="disabled")
        
        try: _load_core()
        except ImportError as e:
            messagebox.showerror("Error", self._("err_deps", str(e)))
            self.btn_scan.configure(state="normal"); self.running = False; return
        
        self._create_backup(dir_)
        self.tree.delete(*self.tree.get_children())
        self.preview_data = []
        self.progress["value"] = 0
        
        def worker():
            data = []; stages = []
            try:
                if self.strat_vars["salary"].get():
                    self.root.after(0, lambda: self._set_status(self._("status_scan_salary")))
                    for o,n in scan_salary(dir_): data.append((o,n,"Salary"))
                    stages.append(f"Salary:{len(data)}")
                
                if self.strat_vars["metadata"].get():
                    self.root.after(0, lambda: self._set_status(self._("status_scan_metadata")))
                    c = len(data)
                    for o,n,s in scan_metadata(dir_): data.append((o,n,s))
                    stages.append(f"Metadata:{len(data)-c}")
                
                if self.strat_vars["archives"].get():
                    self.root.after(0, lambda: self._set_status(self._("status_scan_archives")))
                    c = len(data)
                    for o,n in scan_archives(dir_): data.append((o,n,"Archive"))
                    stages.append(f"Archive:{len(data)-c}")
                
                if self.strat_vars["textfiles"].get():
                    self.root.after(0, lambda: self._set_status(self._("status_scan_text")))
                    c = len(data)
                    for o,n in scan_textfiles(dir_): data.append((o,n,"Text"))
                    stages.append(f"Text:{len(data)-c}")
                
                if self.strat_vars["cluster"].get():
                    self.root.after(0, lambda: self._set_status(self._("status_scan_cluster")))
                    c = len(data)
                    for o,n,s in scan_clusterable(dir_): data.append((o,n,s))
                    stages.append(f"Cluster:{len(data)-c}")
                
                if self.strat_vars["hardcode"].get():
                    self.root.after(0, lambda: self._set_status(self._("status_scan_hardcode")))
                    c = len(data)
                    for o,n,isdir in scan_hardcode(dir_):
                        data.append((o,n,"DirClean" if isdir else "Hardcode"))
                    stages.append(f"Hardcode:{len(data)-c}")
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Scan Error", str(e)))
            
            self.preview_data = data
            self.root.after(0, lambda: self._on_scan_done(data, stages))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _on_scan_done(self, data, stages):
        for i,(o,n,s) in enumerate(data):
            tag = "even" if i%2==0 else "odd"
            self.tree.insert("", "end", values=(i+1, o[:80], n[:80], s), tags=(tag,))
        self._set_status(self._("status_scan_done", len(data), " | ".join(stages) if stages else ""))
        self.count_lbl.configure(text=f"{len(data)} files")
        self.progress["value"] = 100
        self.btn_scan.configure(state="normal")
        self.btn_exec.configure(state="normal" if data else "disabled")
        self.running = False
    
    def _create_backup(self, dir_):
        self.backup_dir = os.path.join(dir_, "_Sisyphus_Backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.backup_dir, f"backup_{ts}.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Name","FullPath","Size","IsDir"])
            for item in os.listdir(dir_):
                ip = os.path.join(dir_, item)
                d = os.path.isdir(ip)
                w.writerow([item, ip, os.path.getsize(ip) if not d else 0, d])
        self._set_status(self._("status_backup_saved", path))
    
    # ======== Export / Clear ========
    def _export(self):
        if not self.preview_data:
            messagebox.showwarning("No Data", self._("err_no_data")); return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV","*.csv")], initialfile="sisyphus_preview.csv")
        if not path: return
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["OldName","NewName","Strategy"])
            for o,n,s in self.preview_data: w.writerow([o,n,s])
        self._set_status(self._("status_exported", path))
    
    def _clear(self):
        self.tree.delete(*self.tree.get_children())
        self.preview_data = []
        self.count_lbl.configure(text="")
        self.btn_exec.configure(state="disabled")
        self._set_status(self._("status_cleared"))
    
    # ======== Execute ========
    def _execute(self):
        if not self.preview_data or self.running: return
        if not messagebox.askyesno(self._("complete_title"),
            self._("confirm_exec", len(self.preview_data))): return
        
        self.running = True
        self.btn_exec.configure(state="disabled")
        self.btn_scan.configure(state="disabled")
        
        dir_ = self.target_dir.get()
        trash = os.path.join(dir_, "_Trash_Duplicates")
        os.makedirs(trash, exist_ok=True)
        self.progress["value"] = 0
        
        def worker():
            _load_core()
            rn=0; dl=0; cl=0; fl=0; total=len(self.preview_data)
            log = []
            
            for i,(old,new,strat) in enumerate(self.preview_data):
                op = os.path.join(dir_, old)
                if not os.path.exists(op):
                    log.append((old,new,"NOT_FOUND",strat)); fl+=1
                elif "/" in new or "\\" in new:
                    parts = new.replace("\\","/").split("/")
                    folder = os.path.join(dir_, parts[0])
                    os.makedirs(folder, exist_ok=True)
                    target = os.path.join(folder, parts[1])
                    try: shutil.move(op, target); cl+=1; log.append((old,new,"CLUSTERED",strat))
                    except Exception as e: fl+=1; log.append((old,new,f"FAIL:{e}",strat))
                else:
                    target = os.path.join(dir_, new)
                    if os.path.exists(target):
                        try:
                            act, alt = resolve_collision(op, target)
                            if act=="DELETE":
                                shutil.move(op, os.path.join(trash,old)); dl+=1
                                log.append((old,new,"DELETED_DUP",strat))
                            else:
                                os.rename(op, os.path.join(dir_,alt)); rn+=1
                                log.append((old,alt,"RENAMED_COL",strat))
                        except Exception as e: fl+=1; log.append((old,new,f"FAIL:{e}",strat))
                    else:
                        try: os.rename(op, target); rn+=1; log.append((old,new,"RENAMED",strat))
                        except Exception as e: fl+=1; log.append((old,new,f"FAIL:{e}",strat))
                
                self.root.after(0, lambda v=int((i+1)/total*100): self.progress.configure(value=v))
            
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = os.path.join(self.backup_dir, f"execution_{ts}.csv")
            with open(log_path,"w",encoding="utf-8-sig",newline="") as f:
                w = csv.writer(f); w.writerow(["OldName","NewName","Action","Strategy"])
                for row in log: w.writerow(row)
            
            self.root.after(0, lambda: self._on_exec_done(rn,dl,cl,fl,log_path))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _on_exec_done(self, rn, dl, cl, fl, log_path):
        messagebox.showinfo(self._("complete_title"),
            self._("complete_msg", rn, dl, cl, fl, log_path))
        self._set_status(self._("status_exec_done", rn, dl, cl))
        self.btn_exec.configure(state="normal")
        self.btn_scan.configure(state="normal")
        self.running = False
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = SisyphusApp()
    app.run()
