"""
WPI Profit Analyser  –  Modern Edition
Author : 1st Year BTech Student
Data   : India Wholesale Price Index (2012-13 to 2022-23)

Libraries needed:
    pip install pandas matplotlib customtkinter

How to run:
    python wpi_analyser_ctk.py
"""

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import matplotlib.cm as cm

# ── Appearance ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Colour palette ────────────────────────────────────────────────────────────
C = {
    "bg"        : "#0f1117",   # deepest background
    "panel"     : "#1a1d2e",   # card / panel bg
    "surface"   : "#252840",   # raised element bg
    "accent"    : "#4f8ef7",   # primary blue accent
    "teal"      : "#2ec4b6",   # profit / sell
    "amber"     : "#f4a261",   # hold
    "red"       : "#e63946",   # loss / avoid
    "txt"       : "#e8eaf6",   # main text
    "txt_dim"   : "#8892b0",   # muted text
    "border"    : "#2e3154",   # subtle border
}

YEARS = [
    "2012-13","2013-14","2014-15","2015-16","2016-17",
    "2017-18","2018-19","2019-20","2020-21","2021-22","2022-23",
]

# ── Matplotlib dark style ─────────────────────────────────────────────────────
MPL_STYLE = {
    "figure.facecolor"  : C["panel"],
    "axes.facecolor"    : C["panel"],
    "axes.edgecolor"    : C["border"],
    "axes.labelcolor"   : C["txt_dim"],
    "xtick.color"       : C["txt_dim"],
    "ytick.color"       : C["txt_dim"],
    "text.color"        : C["txt"],
    "grid.color"        : C["border"],
    "grid.linestyle"    : "--",
    "grid.alpha"        : 0.5,
    "legend.facecolor"  : C["surface"],
    "legend.edgecolor"  : C["border"],
}
plt.rcParams.update(MPL_STYLE)

# ── Treeview (ttk) dark theme ─────────────────────────────────────────────────
def apply_tree_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.Treeview",
        background    = C["panel"],
        foreground    = C["txt"],
        fieldbackground = C["panel"],
        rowheight     = 28,
        font          = ("Segoe UI", 10),
        borderwidth   = 0,
    )
    style.configure("Dark.Treeview.Heading",
        background  = C["surface"],
        foreground  = C["accent"],
        font        = ("Segoe UI", 10, "bold"),
        relief      = "flat",
    )
    style.map("Dark.Treeview",
        background  = [("selected", C["accent"])],
        foreground  = [("selected", "white")],
    )
    style.configure("Dark.Vertical.TScrollbar",
        background   = C["surface"],
        troughcolor  = C["panel"],
        arrowcolor   = C["txt_dim"],
    )
    style.configure("Dark.Horizontal.TScrollbar",
        background   = C["surface"],
        troughcolor  = C["panel"],
        arrowcolor   = C["txt_dim"],
    )

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_data(filepath):
    df = pd.read_csv(filepath)
    df.columns = ["Name","Code","Weight"] + [f"Idx_{y}" for y in YEARS]
    df["Name"]   = df["Name"].str.strip()
    df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")
    for y in YEARS:
        df[f"Idx_{y}"] = pd.to_numeric(df[f"Idx_{y}"], errors="coerce")
    return df

def analyse(df, base_year, compare_year):
    b, c = f"Idx_{base_year}", f"Idx_{compare_year}"
    result = df.copy()
    result["Base"]    = result[b]
    result["Compare"] = result[c]
    result["Change%"] = ((result["Compare"] - result["Base"]) / result["Base"] * 100).round(2)
    def signal(x):
        if x >= 5:   return "SELL (Profit)"
        elif x >= 0: return "Hold"
        else:        return "Avoid (Loss)"
    result["Signal"] = result["Change%"].apply(signal)
    result = result.dropna(subset=["Change%"])
    return result[["Name","Weight","Base","Compare","Change%","Signal"]]


# ══════════════════════════════════════════════════════════════════════════════
#  Main Application
# ══════════════════════════════════════════════════════════════════════════════
class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("WPI Profit Analyser")
        self.geometry("1200x760")
        self.minsize(900, 600)
        self.configure(fg_color=C["bg"])
        apply_tree_style()

        self.df_raw    = None
        self.df_result = None

        self._build_ui()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_controls()
        self._build_kpi_strip()
        self._build_notebook()
        self._build_statusbar()

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=0, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Logo / title
        title_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=8)

        ctk.CTkLabel(
            title_frame, text="📊",
            font=ctk.CTkFont(size=24), text_color=C["accent"]
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            title_frame, text="WPI Profit Analyser",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=C["txt"]
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame, text="  India Wholesale Price Index  2012–2023",
            font=ctk.CTkFont(size=11), text_color=C["txt_dim"]
        ).pack(side="left", padx=(12, 0))

        # Open file button
        ctk.CTkButton(
            hdr, text="  📂  Open CSV File",
            command=self._open_file,
            fg_color=C["accent"], hover_color="#3a7de8",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8, height=36, width=160
        ).pack(side="right", padx=20, pady=11)

    # ── Controls ──────────────────────────────────────────────────────────────
    def _build_controls(self):
        ctrl = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0, height=52)
        ctrl.pack(fill="x", padx=0)
        ctrl.pack_propagate(False)

        inner = ctk.CTkFrame(ctrl, fg_color="transparent")
        inner.pack(side="left", padx=16, pady=8)

        # Base year
        ctk.CTkLabel(inner, text="Base Year", font=ctk.CTkFont(size=11),
                     text_color=C["txt_dim"]).pack(side="left", padx=(0,6))
        self.var_base = ctk.StringVar(value=YEARS[0])
        ctk.CTkComboBox(inner, variable=self.var_base, values=YEARS,
                        state="readonly", width=100,
                        fg_color=C["panel"], border_color=C["border"],
                        button_color=C["accent"], dropdown_fg_color=C["panel"],
                        font=ctk.CTkFont(size=11)
                        ).pack(side="left")

        _sep(inner)

        # Compare year
        ctk.CTkLabel(inner, text="Compare Year", font=ctk.CTkFont(size=11),
                     text_color=C["txt_dim"]).pack(side="left", padx=(0,6))
        self.var_cmp = ctk.StringVar(value=YEARS[-1])
        ctk.CTkComboBox(inner, variable=self.var_cmp, values=YEARS,
                        state="readonly", width=100,
                        fg_color=C["panel"], border_color=C["border"],
                        button_color=C["accent"], dropdown_fg_color=C["panel"],
                        font=ctk.CTkFont(size=11)
                        ).pack(side="left")

        _sep(inner)

        # Search
        ctk.CTkLabel(inner, text="🔍 Search", font=ctk.CTkFont(size=11),
                     text_color=C["txt_dim"]).pack(side="left", padx=(0,6))
        self.var_search = ctk.StringVar()
        ctk.CTkEntry(inner, textvariable=self.var_search, width=160,
                     fg_color=C["panel"], border_color=C["border"],
                     font=ctk.CTkFont(size=11), placeholder_text="Filter by name…"
                     ).pack(side="left")

        _sep(inner)

        # Buttons
        ctk.CTkButton(inner, text="▶  Analyse",
                      command=self._run_analysis,
                      fg_color=C["teal"], hover_color="#25a99d",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      corner_radius=8, height=34, width=110
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(inner, text="⬇  Export CSV",
                      command=self._export,
                      fg_color=C["surface"], hover_color=C["border"],
                      border_width=1, border_color=C["border"],
                      font=ctk.CTkFont(size=11),
                      corner_radius=8, height=34, width=120
                      ).pack(side="left")

    # ── KPI strip ─────────────────────────────────────────────────────────────
    def _build_kpi_strip(self):
        strip = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        strip.pack(fill="x", padx=12, pady=(10, 4))

        kpi_defs = [
            ("total",  "Total Items",   "📦", C["accent"]),
            ("profit", "Sell (Profit)", "📈", C["teal"]),
            ("hold",   "Hold",          "⏸",  C["amber"]),
            ("loss",   "Avoid (Loss)",  "📉", C["red"]),
            ("avg",    "Avg % Change",  "∅",  C["txt_dim"]),
        ]
        self.kpi_labels = {}
        for key, label, icon, color in kpi_defs:
            card = ctk.CTkFrame(strip, fg_color=C["panel"],
                                corner_radius=12, border_width=1,
                                border_color=C["border"])
            card.pack(side="left", expand=True, fill="x", padx=5)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(padx=14, pady=(10, 2), fill="x")
            ctk.CTkLabel(top_row, text=icon,
                         font=ctk.CTkFont(size=16)).pack(side="left")
            ctk.CTkLabel(top_row, text=f"  {label}",
                         font=ctk.CTkFont(size=11),
                         text_color=C["txt_dim"]).pack(side="left")

            val_lbl = ctk.CTkLabel(card, text="—",
                                   font=ctk.CTkFont(size=26, weight="bold"),
                                   text_color=color)
            val_lbl.pack(pady=(0, 12))
            self.kpi_labels[key] = val_lbl

    # ── Notebook ──────────────────────────────────────────────────────────────
    def _build_notebook(self):
        self.nb = ctk.CTkTabview(
            self,
            fg_color=C["panel"],
            segmented_button_fg_color=C["surface"],
            segmented_button_selected_color=C["accent"],
            segmented_button_selected_hover_color="#3a7de8",
            segmented_button_unselected_color=C["surface"],
            segmented_button_unselected_hover_color=C["border"],
            text_color=C["txt"],
            corner_radius=12,
        )
        self.nb.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        tabs = ["All Items", "Best to Sell", "Avoid These", "Bar Chart", "Charts"]
        for t in tabs:
            self.nb.add(t)

        self._build_table(self.nb.tab("All Items"))
        self._build_simple_table(self.nb.tab("Best to Sell"), "profit")
        self._build_simple_table(self.nb.tab("Avoid These"),  "loss")
        self._build_chart_tab(self.nb.tab("Bar Chart"))
        self._build_graphs_tab(self.nb.tab("Charts"))

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_var = ctk.StringVar(value="  Open a CSV file to get started.")
        ctk.CTkLabel(bar, textvariable=self.status_var,
                     font=ctk.CTkFont(size=11), text_color=C["txt_dim"],
                     anchor="w").pack(fill="x", padx=12, pady=4)

    # ── All Items table ───────────────────────────────────────────────────────
    def _build_table(self, parent):
        cols    = ("Name","Weight","Base Index","Compare Index","% Change","Signal")
        widths  = (300, 75, 105, 115, 95, 130)

        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=4, pady=4)

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            style="Dark.Treeview")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col, command=lambda c=col: self._sort(c))
            tree.column(col, width=w,
                        anchor="w" if col == "Name" else "center")

        vsb = ttk.Scrollbar(frame, orient="vertical",
                            command=tree.yview, style="Dark.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(frame, orient="horizontal",
                            command=tree.xview, style="Dark.Horizontal.TScrollbar")
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        _tag_colors(tree)

        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)
        tree.bind("<Double-1>", lambda e: self._show_detail(tree))
        self.tree_all = tree

    # ── Simple table (profit / loss) ──────────────────────────────────────────
    def _build_simple_table(self, parent, kind):
        cols   = ("#","Name","Weight","% Change","Signal")
        widths = (44, 350, 85, 105, 140)

        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=4, pady=4)

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            style="Dark.Treeview")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w,
                        anchor="w" if col == "Name" else "center")

        vsb = ttk.Scrollbar(frame, orient="vertical",
                            command=tree.yview, style="Dark.Vertical.TScrollbar")
        tree.configure(yscrollcommand=vsb.set)
        _tag_colors(tree)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        if kind == "profit":
            self.tree_profit = tree
        else:
            self.tree_loss = tree

    # ── Bar Chart tab ─────────────────────────────────────────────────────────
    def _build_chart_tab(self, parent):
        ctrl = ctk.CTkFrame(parent, fg_color=C["surface"], corner_radius=8)
        ctrl.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(ctrl, fg_color="transparent")
        inner.pack(side="left", padx=12, pady=8)

        ctk.CTkLabel(inner, text="Show Top N", font=ctk.CTkFont(size=11),
                     text_color=C["txt_dim"]).pack(side="left", padx=(0,6))
        self.var_n = ctk.StringVar(value="15")
        ctk.CTkComboBox(inner, variable=self.var_n,
                        values=["10","15","20","30"],
                        state="readonly", width=70,
                        fg_color=C["panel"], border_color=C["border"],
                        button_color=C["accent"],
                        dropdown_fg_color=C["panel"],
                        font=ctk.CTkFont(size=11)
                        ).pack(side="left")

        _sep(inner)

        ctk.CTkLabel(inner, text="Chart Type", font=ctk.CTkFont(size=11),
                     text_color=C["txt_dim"]).pack(side="left", padx=(0,6))
        self.var_chart = ctk.StringVar(value="Top Profit")
        ctk.CTkComboBox(inner, variable=self.var_chart,
                        values=["Top Profit","Top Loss","% Change Distribution"],
                        state="readonly", width=200,
                        fg_color=C["panel"], border_color=C["border"],
                        button_color=C["accent"],
                        dropdown_fg_color=C["panel"],
                        font=ctk.CTkFont(size=11)
                        ).pack(side="left")

        _sep(inner)

        ctk.CTkButton(inner, text="Draw Chart",
                      command=self._draw_chart,
                      fg_color=C["accent"], hover_color="#3a7de8",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      corner_radius=8, height=32, width=110
                      ).pack(side="left")

        self.fig, self.ax = plt.subplots(figsize=(11, 5))
        canvas = FigureCanvasTkAgg(self.fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas = canvas

    # ── Charts tab ────────────────────────────────────────────────────────────
    def _build_graphs_tab(self, parent):
        ctrl = ctk.CTkFrame(parent, fg_color=C["surface"], corner_radius=8)
        ctrl.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(ctrl, fg_color="transparent")
        inner.pack(side="left", padx=12, pady=8)

        ctk.CTkLabel(inner, text="Top N", font=ctk.CTkFont(size=11),
                     text_color=C["txt_dim"]).pack(side="left", padx=(0,6))
        self.var_gn = ctk.StringVar(value="10")
        ctk.CTkComboBox(inner, variable=self.var_gn,
                        values=["5","10","15","20","30"],
                        state="readonly", width=70,
                        fg_color=C["panel"], border_color=C["border"],
                        button_color=C["accent"], dropdown_fg_color=C["panel"],
                        font=ctk.CTkFont(size=11)
                        ).pack(side="left")

        _sep(inner)

        ctk.CTkLabel(inner, text="Graph Type", font=ctk.CTkFont(size=11),
                     text_color=C["txt_dim"]).pack(side="left", padx=(0,6))
        self.var_gtype = ctk.StringVar(value="Bar Graph")
        ctk.CTkComboBox(inner, variable=self.var_gtype,
                        values=["Bar Graph","Histogram","Box Plot","Line Graph"],
                        state="readonly", width=140,
                        fg_color=C["panel"], border_color=C["border"],
                        button_color=C["accent"], dropdown_fg_color=C["panel"],
                        font=ctk.CTkFont(size=11)
                        ).pack(side="left")

        _sep(inner)

        ctk.CTkLabel(inner, text="Show", font=ctk.CTkFont(size=11),
                     text_color=C["txt_dim"]).pack(side="left", padx=(0,6))
        self.var_gshow = ctk.StringVar(value="Best Profit")
        ctk.CTkComboBox(inner, variable=self.var_gshow,
                        values=["Best Profit","Worst Loss","Both"],
                        state="readonly", width=120,
                        fg_color=C["panel"], border_color=C["border"],
                        button_color=C["accent"], dropdown_fg_color=C["panel"],
                        font=ctk.CTkFont(size=11)
                        ).pack(side="left")

        _sep(inner)

        ctk.CTkLabel(inner, text="Item (Line)", font=ctk.CTkFont(size=11),
                     text_color=C["txt_dim"]).pack(side="left", padx=(0,6))
        self.var_gitem = ctk.StringVar()
        ctk.CTkEntry(inner, textvariable=self.var_gitem, width=140,
                     fg_color=C["panel"], border_color=C["border"],
                     font=ctk.CTkFont(size=11), placeholder_text="e.g. wheat"
                     ).pack(side="left")

        _sep(inner)

        ctk.CTkButton(inner, text="Draw",
                      command=self._draw_graphs,
                      fg_color=C["accent"], hover_color="#3a7de8",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      corner_radius=8, height=32, width=80
                      ).pack(side="left")

        self.fig_g = Figure(figsize=(11, 5), facecolor=C["panel"])
        self.ax_g  = self.fig_g.add_subplot(111)
        canvas_g   = FigureCanvasTkAgg(self.fig_g, master=parent)
        NavigationToolbar2Tk(canvas_g, parent)
        canvas_g.get_tk_widget().pack(fill="both", expand=True)
        self.canvas_g = canvas_g

    # ── Actions ───────────────────────────────────────────────────────────────
    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Select WPI CSV file",
            filetypes=[("CSV files","*.csv"),("All files","*.*")]
        )
        if not path:
            return
        try:
            self.df_raw = load_data(path)
            self.status_var.set(
                f"  ✔  Loaded: {path}  |  Rows: {len(self.df_raw)}")
            self._run_analysis()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{e}")

    def _run_analysis(self):
        if self.df_raw is None:
            messagebox.showinfo("No Data", "Please open a CSV file first.")
            return

        base = self.var_base.get()
        cmp  = self.var_cmp.get()

        if YEARS.index(base) >= YEARS.index(cmp):
            messagebox.showwarning(
                "Year Error",
                "Compare year must be AFTER the base year.\n"
                "Example: Base = 2012-13,  Compare = 2022-23"
            )
            return

        df = analyse(self.df_raw, base, cmp)

        q = self.var_search.get().strip().lower()
        if q:
            df = df[df["Name"].str.lower().str.contains(q, na=False)]

        df = df.sort_values("Change%", ascending=False).reset_index(drop=True)
        self.df_result = df

        self._update_kpis()
        self._fill_tables()
        self.status_var.set(
            f"  ✔  Analysis done  |  Base: {base}  →  Compare: {cmp}"
            f"  |  Items: {len(df)}")

    def _update_kpis(self):
        df = self.df_result
        n_profit = (df["Signal"] == "SELL (Profit)").sum()
        n_hold   = (df["Signal"] == "Hold").sum()
        n_loss   = (df["Signal"] == "Avoid (Loss)").sum()
        avg      = df["Change%"].mean()
        self.kpi_labels["total"] .configure(text=str(len(df)))
        self.kpi_labels["profit"].configure(text=str(n_profit))
        self.kpi_labels["hold"]  .configure(text=str(n_hold))
        self.kpi_labels["loss"]  .configure(text=str(n_loss))
        self.kpi_labels["avg"]   .configure(text=f"{avg:+.1f}%")

    def _fill_tables(self):
        df = self.df_result

        # All Items
        self.tree_all.delete(*self.tree_all.get_children())
        for _, row in df.iterrows():
            tag = ("profit" if row["Signal"] == "SELL (Profit)"
                   else "loss" if row["Signal"] == "Avoid (Loss)"
                   else "hold")
            self.tree_all.insert("", "end", tags=(tag,), values=(
                row["Name"][:60],
                f"{row['Weight']:.4f}",
                f"{row['Base']:.1f}"    if pd.notna(row["Base"])    else "—",
                f"{row['Compare']:.1f}" if pd.notna(row["Compare"]) else "—",
                f"{row['Change%']:+.2f}%",
                row["Signal"],
            ))

        # Best to Sell
        top = df[df["Change%"] > 0].head(50).reset_index(drop=True)
        self.tree_profit.delete(*self.tree_profit.get_children())
        for i, row in top.iterrows():
            self.tree_profit.insert("", "end", tags=("profit",), values=(
                i + 1, row["Name"][:60],
                f"{row['Weight']:.4f}",
                f"{row['Change%']:+.2f}%",
                row["Signal"],
            ))

        # Avoid These
        bot = df.tail(50).reset_index(drop=True)
        self.tree_loss.delete(*self.tree_loss.get_children())
        for i, row in bot.iterrows():
            tag = "loss" if row["Signal"] == "Avoid (Loss)" else "hold"
            self.tree_loss.insert("", "end", tags=(tag,), values=(
                i + 1, row["Name"][:60],
                f"{row['Weight']:.4f}",
                f"{row['Change%']:+.2f}%",
                row["Signal"],
            ))

    # ── Bar Chart tab draw ────────────────────────────────────────────────────
    def _draw_chart(self):
        if self.df_result is None:
            messagebox.showinfo("No Data", "Run Analyse first.")
            return

        df   = self.df_result
        n    = int(self.var_n.get())
        kind = self.var_chart.get()
        self.ax.clear()

        if kind == "% Change Distribution":
            vals = df["Change%"].dropna()
            self.ax.hist(vals, bins=35, color=C["accent"],
                         edgecolor=C["bg"], alpha=0.85)
            self.ax.axvline(0, color=C["red"], linestyle="--",
                            linewidth=1.4, label="Break-even (0%)")
            self.ax.axvline(vals.mean(), color=C["amber"], linestyle="--",
                            linewidth=1.4, label=f"Mean ({vals.mean():+.1f}%)")
            self.ax.set_xlabel("% Price Change")
            self.ax.set_ylabel("Number of Commodities")
            self.ax.set_title("Distribution of % Price Changes",
                              color=C["txt"], fontsize=12, fontweight="bold")
            self.ax.legend()

        elif kind == "Top Loss":
            subset = df.nsmallest(n, "Change%")
            bars = self.ax.barh(range(len(subset)),
                                subset["Change%"].values,
                                color=C["red"], edgecolor=C["bg"])
            self.ax.set_yticks(range(len(subset)))
            self.ax.set_yticklabels(
                [nm[:38] for nm in subset["Name"]], fontsize=8.5)
            self.ax.axvline(0, color=C["txt_dim"], linewidth=0.8)
            self.ax.set_xlabel("% Change")
            self.ax.set_title(f"Top {n} Items to AVOID (Lowest % Change)",
                              color=C["txt"], fontsize=12, fontweight="bold")
            self.ax.invert_yaxis()
            for bar, val in zip(bars, subset["Change%"]):
                self.ax.text(bar.get_width() - 0.3,
                             bar.get_y() + bar.get_height() / 2,
                             f"{val:+.1f}%", va="center",
                             ha="right", fontsize=8, color="white")

        else:  # Top Profit
            subset = df.nlargest(n, "Change%")
            bars = self.ax.barh(range(len(subset)),
                                subset["Change%"].values,
                                color=C["teal"], edgecolor=C["bg"])
            self.ax.set_yticks(range(len(subset)))
            self.ax.set_yticklabels(
                [nm[:38] for nm in subset["Name"]], fontsize=8.5)
            self.ax.axvline(0, color=C["txt_dim"], linewidth=0.8)
            self.ax.set_xlabel("% Change")
            self.ax.set_title(f"Top {n} Items to SELL (Highest % Change)",
                              color=C["txt"], fontsize=12, fontweight="bold")
            self.ax.invert_yaxis()
            for bar, val in zip(bars, subset["Change%"]):
                self.ax.text(bar.get_width() + 0.3,
                             bar.get_y() + bar.get_height() / 2,
                             f"{val:+.1f}%", va="center",
                             ha="left", fontsize=8)

        self.ax.grid(True, alpha=0.3)
        self.fig.tight_layout()
        self.canvas.draw()

    # ── Charts tab draw ───────────────────────────────────────────────────────
    def _draw_graphs(self):
        if self.df_result is None:
            messagebox.showinfo("No Data", "Run Analyse first.")
            return
        g = self.var_gtype.get()
        if g == "Bar Graph":    self._draw_g_bar()
        elif g == "Histogram":  self._draw_g_hist()
        elif g == "Box Plot":   self._draw_g_box()
        else:                   self._draw_g_line()

    def _draw_g_bar(self):
        df   = self.df_result
        n    = int(self.var_gn.get())
        show = self.var_gshow.get()
        if show == "Best Profit":
            subset = df.nlargest(n, "Change%")
            colors = [C["teal"]] * len(subset)
            title  = f"Top {n} Items — Best to SELL (Highest % Change)"
        elif show == "Worst Loss":
            subset = df.nsmallest(n, "Change%")
            colors = [C["red"]] * len(subset)
            title  = f"Top {n} Items — AVOID (Lowest % Change)"
        else:
            half   = max(n // 2, 1)
            top    = df.nlargest(half,  "Change%").assign(_c=C["teal"])
            bot    = df.nsmallest(half, "Change%").assign(_c=C["red"])
            subset = pd.concat([top, bot])
            colors = list(subset["_c"])
            title  = f"Top {half} Profit vs Top {half} Loss"

        self.fig_g.clf()
        ax = self.fig_g.add_subplot(111)
        bars = ax.barh(range(len(subset)), subset["Change%"].values,
                       color=colors, edgecolor=C["bg"], height=0.65)
        ax.set_yticks(range(len(subset)))
        ax.set_yticklabels([nm[:40] for nm in subset["Name"]], fontsize=8.5)
        ax.axvline(0, color=C["txt_dim"], linewidth=0.8, linestyle="--")
        ax.set_xlabel("% Price Change")
        ax.set_title(title, fontsize=11, fontweight="bold", color=C["txt"])
        ax.invert_yaxis()
        for bar, val in zip(bars, subset["Change%"]):
            ax.text(bar.get_width() + (0.4 if val >= 0 else -0.4),
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:+.1f}%", va="center",
                    ha="left" if val >= 0 else "right", fontsize=7.5,
                    color=C["txt"])
        ax.legend(handles=[
            mpatches.Patch(facecolor=C["teal"], label="Profit / Sell"),
            mpatches.Patch(facecolor=C["red"],  label="Loss / Avoid"),
        ], fontsize=8)
        self.fig_g.tight_layout()
        self.canvas_g.draw()

    def _draw_g_hist(self):
        vals = self.df_result["Change%"].dropna()
        base = self.var_base.get()
        cmp  = self.var_cmp.get()
        self.fig_g.clf()
        ax = self.fig_g.add_subplot(111)
        ax.hist(vals, bins=40, color=C["accent"],
                edgecolor=C["bg"], alpha=0.85)
        ax.axvline(0,             color=C["red"],   linewidth=1.5,
                   linestyle="--", label="0%  Break-even")
        ax.axvline(vals.mean(),   color=C["amber"], linewidth=1.5,
                   linestyle="--", label=f"Mean  {vals.mean():+.1f}%")
        ax.axvline(vals.median(), color=C["teal"],  linewidth=1.5,
                   linestyle="-.", label=f"Median {vals.median():+.1f}%")
        ax.axvspan(0, vals.max(), alpha=0.05, color=C["teal"])
        ax.axvspan(vals.min(), 0, alpha=0.05, color=C["red"])
        ax.set_xlabel("% Price Change")
        ax.set_ylabel("Number of Commodities")
        ax.set_title(f"Histogram — % Change Distribution  ({base} → {cmp})",
                     fontsize=11, fontweight="bold", color=C["txt"])
        ax.legend(fontsize=8)
        n_p = (vals > 0).sum()
        n_l = (vals < 0).sum()
        ax.text(0.98, 0.97,
                f"Profit items : {n_p}\nLoss items   : {n_l}\nTotal        : {len(vals)}",
                transform=ax.transAxes, va="top", ha="right", fontsize=9,
                bbox=dict(boxstyle="round", facecolor=C["surface"],
                          edgecolor=C["border"], alpha=0.9))
        self.fig_g.tight_layout()
        self.canvas_g.draw()

    def _draw_g_box(self):
        self.fig_g.clf()
        ax   = self.fig_g.add_subplot(111)
        data = [self.df_raw[f"Idx_{y}"].dropna().values for y in YEARS]
        bp   = ax.boxplot(data, labels=YEARS, patch_artist=True,
                          showfliers=False,
                          medianprops=dict(color=C["amber"], linewidth=1.8),
                          whiskerprops=dict(color=C["txt_dim"], linewidth=1),
                          capprops=dict(color=C["txt_dim"], linewidth=1))
        cmap = cm.Blues
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(cmap(0.35 + 0.05 * i))
            patch.set_alpha(0.85)
        means = [self.df_raw[f"Idx_{y}"].mean() for y in YEARS]
        ax.plot(range(1, len(YEARS) + 1), means, "o--",
                color=C["red"], linewidth=1.5, markersize=4, label="Mean index")
        ax.set_xlabel("Year")
        ax.set_ylabel("WPI Index Value")
        ax.set_title("Box Plot — WPI Index Spread Across All Years",
                     fontsize=11, fontweight="bold", color=C["txt"])
        plt.setp(ax.xaxis.get_majorticklabels(),
                 rotation=35, ha="right", fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=8)
        self.fig_g.tight_layout()
        self.canvas_g.draw()

    def _draw_g_line(self):
        query = self.var_gitem.get().strip().lower()
        n     = int(self.var_gn.get())
        items = (
            self.df_raw[self.df_raw["Name"].str.lower()
                        .str.contains(query, na=False)].head(8)
            if query
            else self.df_raw[self.df_raw["Name"].isin(
                self.df_result.nlargest(n, "Change%")["Name"].tolist()
            )].head(n)
        )
        self.fig_g.clf()
        ax = self.fig_g.add_subplot(111)
        if items.empty:
            ax.text(0.5, 0.5, "No matching items found.",
                    ha="center", va="center", transform=ax.transAxes,
                    color=C["txt_dim"], fontsize=12)
            self.canvas_g.draw()
            return
        palette = [C["accent"], C["teal"], C["red"], C["amber"],
                   "#c77dff", "#06d6a0", "#ffd166", "#ef476f"]
        for i, (_, row) in enumerate(items.iterrows()):
            vals = [row.get(f"Idx_{y}") for y in YEARS]
            clr  = palette[i % len(palette)]
            ax.plot(YEARS, vals, marker="o", linewidth=2,
                    markersize=5, color=clr, label=row["Name"][:30])
            last = next((v for v in reversed(vals) if pd.notna(v)), None)
            if last:
                ax.annotate(f"{last:.0f}", (YEARS[-1], last),
                            textcoords="offset points", xytext=(5, 0),
                            fontsize=7.5, color=clr)
        ax.set_xlabel("Year")
        ax.set_ylabel("WPI Index")
        ax.set_title("Line Graph — Year-by-Year WPI Index Trend",
                     fontsize=11, fontweight="bold", color=C["txt"])
        plt.setp(ax.xaxis.get_majorticklabels(),
                 rotation=35, ha="right", fontsize=8)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper left", ncol=2)
        self.fig_g.tight_layout()
        self.canvas_g.draw()

    # ── Double-click detail window ────────────────────────────────────────────
    def _show_detail(self, tree):
        sel = tree.selection()
        if not sel:
            return
        name      = tree.item(sel[0], "values")[0]
        row_match = self.df_raw[self.df_raw["Name"].str.startswith(name[:20])]
        if row_match.empty:
            return
        row  = row_match.iloc[0]
        vals = [row.get(f"Idx_{y}", None) for y in YEARS]
        yrs  = [y for y, v in zip(YEARS, vals) if pd.notna(v)]
        vals = [v for v in vals if pd.notna(v)]

        win = ctk.CTkToplevel(self)
        win.title(f"Trend — {name[:50]}")
        win.geometry("700x440")
        win.configure(fg_color=C["bg"])

        ctk.CTkLabel(win, text=name,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["txt"], wraplength=660,
                     justify="left").pack(padx=18, pady=(14, 6), anchor="w")

        fig2, ax2 = plt.subplots(figsize=(8.5, 4.2))
        fig2.patch.set_facecolor(C["panel"])
        ax2.plot(yrs, vals, marker="o", color=C["accent"],
                 linewidth=2, markersize=5)
        ax2.fill_between(range(len(vals)), vals,
                         alpha=0.15, color=C["teal"])
        ax2.set_xticks(range(len(yrs)))
        ax2.set_xticklabels(yrs, rotation=35, ha="right", fontsize=8)
        ax2.set_ylabel("WPI Index")
        ax2.set_title("Historical WPI Index", color=C["txt"],
                      fontsize=11, fontweight="bold")
        ax2.grid(True, alpha=0.3)
        fig2.tight_layout()

        c2 = FigureCanvasTkAgg(fig2, master=win)
        c2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=6)

    # ── Sort ──────────────────────────────────────────────────────────────────
    def _sort(self, col):
        if self.df_result is None:
            return
        col_map = {
            "Name": "Name", "Weight": "Weight",
            "Base Index": "Base", "Compare Index": "Compare",
            "% Change": "Change%", "Signal": "Signal",
        }
        key = col_map.get(col, "Change%")
        asc = key in ("Name", "Signal")
        self.df_result = self.df_result.sort_values(
            key, ascending=asc).reset_index(drop=True)
        self._fill_tables()

    # ── Export ────────────────────────────────────────────────────────────────
    def _export(self):
        if self.df_result is None:
            messagebox.showinfo("No Data", "Run Analyse first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv")],
            initialfile="wpi_analysis_result.csv"
        )
        if path:
            self.df_result.to_csv(path, index=False)
            messagebox.showinfo("Saved", f"File saved to:\n{path}")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _sep(parent):
    """Thin vertical separator."""
    ctk.CTkFrame(parent, width=1, height=24,
                 fg_color=C["border"]).pack(side="left", padx=10)

def _tag_colors(tree):
    tree.tag_configure("profit", foreground=C["teal"])
    tree.tag_configure("hold",   foreground=C["amber"])
    tree.tag_configure("loss",   foreground=C["red"])


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
