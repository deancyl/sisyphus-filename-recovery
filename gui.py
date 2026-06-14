"""
Sisyphus v1.1.0 - Universal Garbled Filename Recovery GUI
Pure tkinter, i18n zh/en, config-driven pipeline
"""
import os, sys, threading, datetime, csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.i18n import i18n as _i18n
from core.system_check import get_status
from core.pipeline import run_full_scan, execute_renames, load_config

class SisyphusApp:
    def __init__(self):
        self.root = tk.Tk()
        self._ = _i18n.get
        self.root.title(self._("title"))
        self.root.geometry("1100x700")
        self.root.minsize(800, 500)
        
        self.target_dir = tk.StringVar(value=os.path.expanduser("~\\Downloads"))
        self.config_path = tk.StringVar(value="")
        self.preview_data = []
        self.backup_dir = ""
        self.running = False
        
        self._build_ui()
        self._check_system()
    
    def _build_ui(self):
        r = self.root
        r.grid_columnconfigure(0, weight=1)
        r.grid_rowconfigure(3, weight=1)
        
        # Row 0: Directory + Config + Language + ACP
        top = ttk.Frame(r, padding=5)
        top.grid(row=0, column=0, sticky="ew")
        
        ttk.Label(top, text=self._("target_label")).pack(side="left", padx=(5,2))
        ttk.Entry(top, textvariable=self.target_dir, width=50).pack(side="left", padx=2)
        ttk.Button(top, text=self._("browse"), command=self._browse).pack(side="left", padx=2)
        
        # Config file
        ttk.Label(top, text="Config:").pack(side="left", padx=(10,2))
        cfg_entry = ttk.Entry(top, textvariable=self.config_path, width=20)
        cfg_entry.pack(side="left", padx=2)
        ttk.Button(top, text="...", width=3, command=self._browse_config).pack(side="left")
        
        # Language
        lang_frame = ttk.Frame(top)
        lang_frame.pack(side="right", padx=10)
        ttk.Label(lang_frame, text=self._("lang_label")).pack(side="left")
        self.lang_var = tk.StringVar(value=_i18n.lang)
        ttk.Combobox(lang_frame, textvariable=self.lang_var, values=_i18n.get_all_langs(),
                      width=4, state="readonly").pack(side="left", padx=2)
        self.lang_var.trace("w", self._on_lang_change)
        
        self.sys_label = ttk.Label(top, text="", foreground="gray")
        self.sys_label.pack(side="right", padx=10)
        
        # Row 1: Strategy description
        sf = ttk.LabelFrame(r, text=self._("strategies_label"), padding=5)
        sf.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        info = ("Pipeline: Hardcode Mappings → Metadata Extraction → "
                "Regex Rules → Generic Sanitizer → Fallback Cluster")
        ttk.Label(sf, text=info, font=("", 9)).pack(side="left", padx=10)
        
        # Row 2: Buttons
        bf = ttk.Frame(r, padding=5)
        bf.grid(row=2, column=0, sticky="ew")
        
        self.btn_scan = ttk.Button(bf, text=self._("btn_scan"), command=self._scan, width=18)
        self.btn_scan.pack(side="left", padx=5)
        self.btn_exec = ttk.Button(bf, text=self._("btn_execute"), command=self._execute, width=18, state="disabled")
        self.btn_exec.pack(side="left", padx=5)
        ttk.Button(bf, text=self._("btn_export"), command=self._export, width=18).pack(side="left", padx=5)
        ttk.Button(bf, text=self._("btn_clear"), command=self._clear, width=18).pack(side="left", padx=5)
        ttk.Button(bf, text=self._("btn_about"), command=self._about, width=12).pack(side="right", padx=5)
        
        self.count_lbl = ttk.Label(bf, text="")
        self.count_lbl.pack(side="right", padx=10)
        
        # Row 3: Treeview
        tf = ttk.Frame(r)
        tf.grid(row=3, column=0, sticky="nsew", padx=5, pady=2)
        tf.grid_columnconfigure(0, weight=1)
        tf.grid_rowconfigure(0, weight=1)
        
        cols = ("#", "Old Name", "New Name", "Strategy")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="extended", height=18)
        for c, key in zip(cols, ["col_num","col_old","col_new","col_strategy"]):
            self.tree.heading(c, text=self._(key))
        self.tree.column("#", width=40, anchor="center")
        self.tree.column("Old Name", width=360)
        self.tree.column("New Name", width=360)
        self.tree.column("Strategy", width=120)
        
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.tag_configure("even", background="#f0f0f0")
        self.tree.tag_configure("odd", background="white")
        
        # Row 4: Status
        sf2 = ttk.Frame(r, padding=3)
        sf2.grid(row=4, column=0, sticky="ew")
        self.status_lbl = ttk.Label(sf2, text=self._("status_ready"), relief="sunken", anchor="w", padding=2)
        self.status_lbl.pack(side="top", fill="x")
        self.progress = ttk.Progressbar(sf2, mode="determinate")
        self.progress.pack(side="bottom", fill="x", pady=2)
    
    def _on_lang_change(self, *a):
        new = self.lang_var.get()
        if new != _i18n.lang:
            messagebox.showinfo("Language", "Restart to apply language change.")
            self.lang_var.set(_i18n.lang)
    
    def _set_status(self, msg):
        self.status_lbl.configure(text=msg); self.root.update_idletasks()
    
    def _browse(self):
        p = filedialog.askdirectory(title="Target Directory")
        if p: self.target_dir.set(p)
    
    def _browse_config(self):
        p = filedialog.askopenfilename(title="Select Config YAML",
            filetypes=[("YAML","*.yaml;*.yml"),("All","*.*")])
        if p: self.config_path.set(p)
    
    def _check_system(self):
        try:
            s = get_status()
            colors = {"ok":"green","warning":"orange","error":"red"}
            tag = self._("acp_ok") if s["status"]=="ok" else self._("acp_warn")
            self.sys_label.configure(text=f"ACP: {s['acp']} - {tag}",
                foreground=colors.get(s["status"],"black"))
        except Exception as e:
            self.sys_label.configure(text=f"ACP: ? - {e}", foreground="red")
    
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
    
    def _scan(self):
        if self.running: return
        dir_ = self.target_dir.get()
        if not os.path.isdir(dir_):
            messagebox.showerror("Error", self._("err_invalid_dir")+"\n"+dir_); return
        
        self.running = True
        self._set_status(self._("status_loading"))
        self.btn_scan.configure(state="disabled")
        
        self._create_backup(dir_)
        self.tree.delete(*self.tree.get_children())
        self.preview_data = []
        self.progress["value"] = 0
        
        # Load config
        config = None
        cfg = self.config_path.get()
        if cfg and os.path.exists(cfg):
            config = load_config(cfg)
        else:
            config = load_config()
        
        def worker():
            try:
                records = run_full_scan(dir_, config)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Scan Error", str(e)))
                records = []
            self.preview_data = records
            self.root.after(0, lambda: self._on_scan_done(records))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _on_scan_done(self, data):
        for i,(o,n,s) in enumerate(data):
            tag = "even" if i%2==0 else "odd"
            self.tree.insert("", "end", values=(i+1, o[:80], n[:80], s), tags=(tag,))
        self._set_status(self._("status_scan_done", len(data), ""))
        self.count_lbl.configure(text=f"{len(data)} files")
        self.progress["value"] = 100
        self.btn_scan.configure(state="normal")
        self.btn_exec.configure(state="normal" if data else "disabled")
        self.running = False
    
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
    
    def _execute(self):
        if not self.preview_data or self.running: return
        if not messagebox.askyesno(self._("complete_title"),
            self._("confirm_exec", len(self.preview_data))): return
        
        self.running = True
        self.btn_exec.configure(state="disabled"); self.btn_scan.configure(state="disabled")
        dir_ = self.target_dir.get()
        self.progress["value"] = 0
        
        def worker():
            rn, dl, cl, fl, log_path = execute_renames(dir_, self.preview_data, self.backup_dir)
            self.root.after(0, lambda: self._on_exec_done(rn, dl, cl, fl, log_path))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _on_exec_done(self, rn, dl, cl, fl, log_path):
        messagebox.showinfo(self._("complete_title"),
            self._("complete_msg", rn, dl, cl, fl, log_path))
        self._set_status(self._("status_exec_done", rn, dl, cl))
        self.btn_exec.configure(state="normal"); self.btn_scan.configure(state="normal")
        self.running = False
    
    def _about(self):
        messagebox.showinfo("Sisyphus v1.1.0",
            "Universal Garbled Filename Recovery\n\n"
            "Pipeline: Hardcode → Metadata → Regex → Sanitizer → Fallback\n"
            "github.com/deancyl/sisyphus-filename-recovery")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SisyphusApp(); app.run()
