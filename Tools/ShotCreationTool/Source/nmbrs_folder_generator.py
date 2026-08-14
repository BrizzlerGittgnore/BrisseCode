"""
NMBRS Folder Structure Generator
A tool to generate and manage VFX/CG project folder structures.
"""

import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# ─── Config ────────────────────────────────────────────────────────────────────

CONFIG_FILENAME = "nmbrs_project.json"
MAYA_TEMPLATE_FILENAME = "SQ01_sh0010_v001.ma"
MAYA_TEMPLATE_SHOT_NAME = "SQ01_sh0010"

DEFAULT_PROJECT = {
    "project_name": "MyProject",
    "root_path": "",
    "sequences": [],
    "frame_rate": 24
}

# ─── Folder Templates ─────────────────────────────────────────────────────────

STATIC_STRUCTURE = {
    "01_Preproduction": {
        "01_Treatment": {},
        "02_Script": {},
        "03_StoryBoard": {},
        "04_FromClient": {}
    },
    "02_Assets": {
        "01_Characters": {
            "Copy_ME": {
                "01_Geo": {"v001": {}},
                "02_Texture": {"v001": {}},
                "03_Rig": {},
                "04_Out": {"v001": {}}
            }
        },
        "02_Environments": {
            "01_Geo": {"v001": {}},
            "02_Texture": {"v001": {}},
            "03_Out": {"v001": {}}
        },
        "03_MarketPlace": {}
    },
    "03_Shots": {},
    "04_Post": {
        "01_Comp": {},
        "02_Edit": {}
    },
    "05_Out": {
        "01_Dailies": {},
        "02_Animatic": {}
    },
    "06_Delivery": {}
}

SHOT_TEMPLATE = {
    "01_Maya": {"export": {"v001": {}}},
    "02_hip": {"export": {"v001": {}}},
    "03_UE_render": {"v001": {}},
    "04_2DGraphics": {"v001": {}},
    "05_2DFX": {"v001": {}}
}


# ─── Core Logic ────────────────────────────────────────────────────────────────

def get_maya_template_path() -> str:
    """Get the Maya template file path relative to this script."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), MAYA_TEMPLATE_FILENAME)


def create_maya_file(shot_path: str, shot_name: str):
    """Create a Maya file from the template with the shot name replaced."""
    template_path = get_maya_template_path()
    if not os.path.isfile(template_path):
        return
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace(MAYA_TEMPLATE_SHOT_NAME, shot_name)
    maya_dir = os.path.join(shot_path, "01_Maya")
    os.makedirs(maya_dir, exist_ok=True)
    maya_file = os.path.join(maya_dir, f"{shot_name}_v001.ma")
    with open(maya_file, "w", encoding="utf-8") as f:
        f.write(content)


def create_folders(base_path: str, structure: dict):
    """Recursively create folders from a nested dict."""
    for name, children in structure.items():
        folder = os.path.join(base_path, name)
        os.makedirs(folder, exist_ok=True)
        if children:
            create_folders(folder, children)


def shot_folder_name(seq_num: int, shot_num: int) -> str:
    """Return formatted shot folder name like SQ01_sh0010."""
    return f"SQ{seq_num:02d}_sh{shot_num:04d}"


def generate_full_structure(root_path: str, sequences: list):
    """Generate the complete project folder structure including all shots."""
    create_folders(root_path, STATIC_STRUCTURE)
    shots_root = os.path.join(root_path, "03_Shots")
    for seq in sequences:
        seq_num = seq["sequence"]
        for shot in seq["shots"]:
            shot_name = shot_folder_name(seq_num, shot["shot"])
            shot_path = os.path.join(shots_root, shot_name)
            create_folders(shot_path, SHOT_TEMPLATE)
            create_maya_file(shot_path, shot_name)


def generate_single_shot(root_path: str, seq_num: int, shot_num: int):
    """Generate a single shot folder inside 03_Shots."""
    shots_root = os.path.join(root_path, "03_Shots")
    os.makedirs(shots_root, exist_ok=True)
    shot_name = shot_folder_name(seq_num, shot_num)
    shot_path = os.path.join(shots_root, shot_name)
    create_folders(shot_path, SHOT_TEMPLATE)
    create_maya_file(shot_path, shot_name)
    return shot_name


def load_config(root_path: str) -> dict:
    """Load project config JSON from root path."""
    config_path = os.path.join(root_path, CONFIG_FILENAME)
    if os.path.isfile(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_config(root_path: str, config: dict):
    """Save project config JSON to root path."""
    os.makedirs(root_path, exist_ok=True)
    config_path = os.path.join(root_path, CONFIG_FILENAME)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ─── GUI ───────────────────────────────────────────────────────────────────────

class NMBRSGeneratorApp:
    BG = "#1e1e2e"
    BG_CARD = "#2a2a3d"
    BG_INPUT = "#363650"
    FG = "#cdd6f4"
    FG_DIM = "#6c7086"
    ACCENT = "#89b4fa"
    ACCENT_HOVER = "#74c7ec"
    GREEN = "#a6e3a1"
    RED = "#f38ba8"
    YELLOW = "#f9e2af"
    BORDER = "#45475a"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("NMBRS Folder Structure Generator")
        self.root.geometry("900x720")
        self.root.minsize(780, 650)
        self.root.configure(bg=self.BG)

        self.config = dict(DEFAULT_PROJECT)
        self.sequences_data = []  # list of {sequence, shots: [{shot, frames}]}

        self._setup_styles()
        self._build_ui()
        self._bind_keys()

    # ── Styles ─────────────────────────────────────────────────────────────

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=self.BG, foreground=self.FG, borderwidth=0)
        style.configure("TFrame", background=self.BG)
        style.configure("Card.TFrame", background=self.BG_CARD)
        style.configure("TLabel", background=self.BG, foreground=self.FG, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=self.ACCENT)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 12, "bold"), foreground=self.FG)
        style.configure("Dim.TLabel", foreground=self.FG_DIM, font=("Segoe UI", 9))
        style.configure("Status.TLabel", foreground=self.GREEN, font=("Segoe UI", 9))

        # Buttons
        style.configure("Accent.TButton",
                        background=self.ACCENT, foreground="#1e1e2e",
                        font=("Segoe UI", 10, "bold"), padding=(16, 8))
        style.map("Accent.TButton",
                  background=[("active", self.ACCENT_HOVER), ("disabled", self.BG_INPUT)])

        style.configure("Green.TButton",
                        background=self.GREEN, foreground="#1e1e2e",
                        font=("Segoe UI", 10, "bold"), padding=(16, 8))
        style.map("Green.TButton",
                  background=[("active", "#94e2d5"), ("disabled", self.BG_INPUT)])

        style.configure("Secondary.TButton",
                        background=self.BG_INPUT, foreground=self.FG,
                        font=("Segoe UI", 9), padding=(10, 5))
        style.map("Secondary.TButton",
                  background=[("active", self.BORDER)])

        style.configure("Danger.TButton",
                        background=self.RED, foreground="#1e1e2e",
                        font=("Segoe UI", 9), padding=(8, 4))
        style.map("Danger.TButton",
                  background=[("active", "#eba0ac")])

        # Entry
        style.configure("TEntry", fieldbackground=self.BG_INPUT, foreground=self.FG,
                        insertcolor=self.FG, padding=6)
        style.map("TEntry", fieldbackground=[("focus", self.BG_INPUT)])

        # Spinbox
        style.configure("TSpinbox", fieldbackground=self.BG_INPUT, foreground=self.FG,
                        arrowcolor=self.ACCENT, padding=4)

        # Separator
        style.configure("TSeparator", background=self.BORDER)

        # Treeview — hierarchical with tree column visible
        style.configure("Treeview",
                        background=self.BG_CARD, foreground=self.FG,
                        fieldbackground=self.BG_CARD, borderwidth=0,
                        font=("Segoe UI", 9), rowheight=26, indent=20)
        style.configure("Treeview.Heading",
                        background=self.BG_INPUT, foreground=self.ACCENT,
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
                  background=[("selected", self.ACCENT)],
                  foreground=[("selected", "#1e1e2e")])

    # ── Build UI ───────────────────────────────────────────────────────────

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(main)
        header_frame.pack(fill="x", pady=(0, 12))
        ttk.Label(header_frame, text="NMBRS Folder Generator", style="Header.TLabel").pack(side="left")

        # ── Project Path ───────────────────────────────────────────────────
        path_card = self._card(main)
        path_card.pack(fill="x", pady=(0, 10))

        ttk.Label(path_card, text="Project Root", style="SubHeader.TLabel").pack(anchor="w")
        ttk.Label(path_card, text="Choose the root directory where the project structure will be created",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 6))

        path_row = ttk.Frame(path_card, style="Card.TFrame")
        path_row.pack(fill="x")

        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(path_row, textvariable=self.path_var, font=("Segoe UI", 10))
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ttk.Button(path_row, text="Browse…", style="Secondary.TButton",
                   command=self._browse_path).pack(side="left", padx=(0, 4))
        ttk.Button(path_row, text="Load Config", style="Secondary.TButton",
                   command=self._load_existing_config).pack(side="left")

        # ── Add Shots ──────────────────────────────────────────────────────
        add_card = self._card(main)
        add_card.pack(fill="x", pady=(0, 10))

        ttk.Label(add_card, text="Add Shots", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 8))

        # Row 1 — Single shot creation
        single_row = ttk.Frame(add_card, style="Card.TFrame")
        single_row.pack(fill="x", pady=(0, 6))

        ttk.Label(single_row, text="SQ:", style="Card.TLabel").pack(side="left", padx=(0, 2))
        self.seq_var = tk.IntVar(value=1)
        ttk.Spinbox(single_row, from_=1, to=99, textvariable=self.seq_var,
                     width=5, font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))

        ttk.Label(single_row, text="Shot:", style="Card.TLabel").pack(side="left", padx=(0, 2))
        self.shot_var = tk.IntVar(value=10)
        ttk.Spinbox(single_row, from_=10, to=9990, increment=10,
                     textvariable=self.shot_var, width=6, font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))

        ttk.Label(single_row, text="Frames:", style="Card.TLabel").pack(side="left", padx=(0, 2))
        self.frames_var = tk.IntVar(value=100)
        ttk.Spinbox(single_row, from_=1, to=99999,
                     textvariable=self.frames_var, width=7, font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))

        ttk.Button(single_row, text="+ Add Shot", style="Accent.TButton",
                   command=self._add_shot).pack(side="left")

        # Row 2 — Batch shot creation
        batch_row = ttk.Frame(add_card, style="Card.TFrame")
        batch_row.pack(fill="x")

        ttk.Label(batch_row, text="SQ:", style="Card.TLabel").pack(side="left", padx=(0, 2))
        self.batch_seq_var = tk.IntVar(value=1)
        ttk.Spinbox(batch_row, from_=1, to=99, textvariable=self.batch_seq_var,
                     width=5, font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))

        ttk.Label(batch_row, text="Count:", style="Card.TLabel").pack(side="left", padx=(0, 2))
        self.batch_count_var = tk.IntVar(value=5)
        ttk.Spinbox(batch_row, from_=1, to=999, textvariable=self.batch_count_var,
                     width=5, font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))

        ttk.Label(batch_row, text="Start at:", style="Card.TLabel").pack(side="left", padx=(0, 2))
        self.batch_start_var = tk.IntVar(value=10)
        ttk.Spinbox(batch_row, from_=10, to=9990, increment=10,
                     textvariable=self.batch_start_var, width=6, font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))

        ttk.Label(batch_row, text="Frames:", style="Card.TLabel").pack(side="left", padx=(0, 2))
        self.batch_frames_var = tk.IntVar(value=100)
        ttk.Spinbox(batch_row, from_=1, to=99999,
                     textvariable=self.batch_frames_var, width=7, font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))

        ttk.Button(batch_row, text="+ Batch Add", style="Green.TButton",
                   command=self._add_batch_shots).pack(side="left")

        # ── Hierarchy Tree ─────────────────────────────────────────────────
        tree_card = self._card(main)
        tree_card.pack(fill="both", expand=True, pady=(0, 10))

        tree_header = ttk.Frame(tree_card, style="Card.TFrame")
        tree_header.pack(fill="x", pady=(0, 6))
        ttk.Label(tree_header, text="Shot Hierarchy", style="SubHeader.TLabel").pack(side="left")
        ttk.Label(tree_header, text="Right-click or press Delete to remove items",
                  style="Dim.TLabel").pack(side="right")

        tree_frame = ttk.Frame(tree_card, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True)

        cols = ("folder_name", "frames")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="tree headings",
                                 selectmode="extended")
        self.tree.heading("#0", text="Hierarchy", anchor="w")
        self.tree.heading("folder_name", text="Folder Name")
        self.tree.heading("frames", text="Frames")
        self.tree.column("#0", width=200, anchor="w")
        self.tree.column("folder_name", width=220, anchor="w")
        self.tree.column("frames", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Context menu
        self.ctx_menu = tk.Menu(self.root, tearoff=0,
                                bg=self.BG_CARD, fg=self.FG,
                                activebackground=self.ACCENT, activeforeground="#1e1e2e",
                                font=("Segoe UI", 9))
        self.ctx_menu.add_command(label="Delete", command=self._delete_selected)

        self.tree.bind("<Button-3>", self._show_context_menu)

        # ── Bottom Bar ─────────────────────────────────────────────────────
        bottom = ttk.Frame(main)
        bottom.pack(fill="x", pady=(0, 0))

        ttk.Button(bottom, text="Generate Folders", style="Green.TButton",
                   command=self._generate_all).pack(side="left", padx=(0, 8))
        ttk.Button(bottom, text="Save Config", style="Secondary.TButton",
                   command=self._save_config_action).pack(side="right")

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(bottom, textvariable=self.status_var, style="Status.TLabel").pack(side="left", padx=(16, 0))

    def _card(self, parent) -> ttk.Frame:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        return card

    # ── Key Bindings ───────────────────────────────────────────────────────

    def _bind_keys(self):
        self.tree.bind("<Delete>", lambda e: self._delete_selected())

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.ctx_menu.tk_popup(event.x_root, event.y_root)

    # ── Tree helpers ───────────────────────────────────────────────────────

    def _get_seq_node(self, seq_num: int) -> str:
        """Find or create a sequence parent node. Returns tree item id."""
        seq_text = f"SQ{seq_num:02d}"
        for child in self.tree.get_children(""):
            if self.tree.item(child, "text") == seq_text:
                return child
        # Create new sequence node
        node = self.tree.insert("", "end", text=seq_text,
                                values=(f"Sequence {seq_num:02d}", ""),
                                open=True, tags=("sequence",))
        return node

    def _shot_exists(self, seq_num: int, shot_num: int) -> bool:
        """Check if a shot already exists under its sequence node."""
        seq_node = None
        seq_text = f"SQ{seq_num:02d}"
        for child in self.tree.get_children(""):
            if self.tree.item(child, "text") == seq_text:
                seq_node = child
                break
        if seq_node is None:
            return False
        name = shot_folder_name(seq_num, shot_num)
        for shot_item in self.tree.get_children(seq_node):
            if self.tree.item(shot_item, "values")[0] == name:
                return True
        return False

    def _insert_shot(self, seq_num: int, shot_num: int, frames: int):
        """Insert a shot node under the correct sequence, sorted by shot number."""
        name = shot_folder_name(seq_num, shot_num)
        seq_node = self._get_seq_node(seq_num)

        # Find correct sorted position
        children = self.tree.get_children(seq_node)
        insert_index = "end"
        for i, child in enumerate(children):
            child_name = self.tree.item(child, "values")[0]
            # Extract shot number from folder name for comparison
            try:
                existing_shot = int(child_name.split("_sh")[1])
            except (IndexError, ValueError):
                continue
            if shot_num < existing_shot:
                insert_index = i
                break

        shot_text = f"sh{shot_num:04d}"
        self.tree.insert(seq_node, insert_index, text=shot_text,
                         values=(name, frames), tags=("shot",))

    def _refresh_tree_from_data(self):
        """Clear and rebuild the tree from sequences_data."""
        self.tree.delete(*self.tree.get_children())
        for seq in self.sequences_data:
            for shot in seq.get("shots", []):
                self._insert_shot(seq["sequence"], shot["shot"], shot.get("frames", 0))

    def _rebuild_sequences_data(self):
        """Rebuild sequences_data from treeview hierarchy."""
        self.sequences_data = []
        for seq_node in self.tree.get_children(""):
            seq_text = self.tree.item(seq_node, "text")  # e.g. "SQ01"
            try:
                seq_num = int(seq_text.replace("SQ", ""))
            except ValueError:
                continue
            shots = []
            for shot_item in self.tree.get_children(seq_node):
                vals = self.tree.item(shot_item, "values")
                folder_name = vals[0]  # e.g. "SQ01_sh0010"
                frames = int(vals[1]) if vals[1] else 0
                try:
                    shot_num = int(folder_name.split("_sh")[1])
                except (IndexError, ValueError):
                    continue
                shots.append({"shot": shot_num, "frames": frames})
            if shots:
                self.sequences_data.append({
                    "sequence": seq_num,
                    "shots": sorted(shots, key=lambda s: s["shot"])
                })
        self.sequences_data.sort(key=lambda s: s["sequence"])

    # ── Actions ────────────────────────────────────────────────────────────

    def _browse_path(self):
        path = filedialog.askdirectory(title="Select Project Root Folder")
        if path:
            self.path_var.set(path)
            cfg = load_config(path)
            if cfg:
                self._apply_config(cfg)
                self._set_status("Config loaded from existing project")

    def _load_existing_config(self):
        root_path = self.path_var.get().strip()
        if not root_path:
            messagebox.showwarning("No Path", "Please set a project root path first.")
            return
        cfg = load_config(root_path)
        if cfg:
            self._apply_config(cfg)
            self._set_status("Config loaded successfully")
        else:
            messagebox.showinfo("No Config", f"No {CONFIG_FILENAME} found in the selected folder.")

    def _apply_config(self, cfg: dict):
        self.config = cfg
        if cfg.get("root_path"):
            self.path_var.set(cfg["root_path"])
        self.sequences_data = cfg.get("sequences", [])
        self._refresh_tree_from_data()

    def _add_shot(self):
        seq_num = self.seq_var.get()
        shot_num = self.shot_var.get()
        frames = self.frames_var.get()
        name = shot_folder_name(seq_num, shot_num)

        if self._shot_exists(seq_num, shot_num):
            messagebox.showwarning("Duplicate", f"{name} already exists.")
            return

        self._insert_shot(seq_num, shot_num, frames)
        self._rebuild_sequences_data()
        self._set_status(f"Added {name} ({frames} frames)")
        self.shot_var.set(shot_num + 10)

    def _add_batch_shots(self):
        seq_num = self.batch_seq_var.get()
        count = self.batch_count_var.get()
        start = self.batch_start_var.get()
        frames = self.batch_frames_var.get()

        added = 0
        skipped = 0
        for i in range(count):
            shot_num = start + i * 10
            if self._shot_exists(seq_num, shot_num):
                skipped += 1
                continue
            self._insert_shot(seq_num, shot_num, frames)
            added += 1

        self._rebuild_sequences_data()
        msg = f"Batch: added {added} shots to SQ{seq_num:02d}"
        if skipped:
            msg += f" ({skipped} skipped — duplicates)"
        self._set_status(msg)

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        for item in selected:
            # If deleting a sequence node, all its shots go too
            self.tree.delete(item)
        # Clean up empty sequence nodes
        for seq_node in self.tree.get_children(""):
            if not self.tree.get_children(seq_node):
                self.tree.delete(seq_node)
        self._rebuild_sequences_data()
        self._set_status("Deleted selected items")

    def _get_root_path(self) -> str:
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("No Path", "Please set a project root path first.")
            return ""
        return path

    def _build_config(self) -> dict:
        self._rebuild_sequences_data()
        return {
            "project_name": self.config.get("project_name", "MyProject"),
            "root_path": self.path_var.get().strip(),
            "sequences": self.sequences_data,
            "frame_rate": self.config.get("frame_rate", 24)
        }

    def _generate_all(self):
        root_path = self._get_root_path()
        if not root_path:
            return
        self._rebuild_sequences_data()

        if not self.sequences_data:
            resp = messagebox.askyesno("No Shots",
                                       "No shots configured. Generate base structure without shots?")
            if not resp:
                return

        try:
            generate_full_structure(root_path, self.sequences_data)
            cfg = self._build_config()
            save_config(root_path, cfg)
            total = sum(len(s["shots"]) for s in self.sequences_data)
            self._set_status(f"✓ Structure generated — {total} shots. Config saved.")
            messagebox.showinfo("Done",
                                f"Project created at:\n{root_path}\n\n"
                                f"{total} shot(s) generated.\nConfig saved as {CONFIG_FILENAME}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_config_action(self):
        root_path = self._get_root_path()
        if not root_path:
            return
        cfg = self._build_config()
        try:
            save_config(root_path, cfg)
            self._set_status(f"✓ Config saved to {CONFIG_FILENAME}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _set_status(self, text: str):
        self.status_var.set(text)


# ─── Entry Point ───────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    root.tk_setPalette(background="#1e1e2e", foreground="#cdd6f4")

    # Set window icon (optional, skip gracefully)
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = NMBRSGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
