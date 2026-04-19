"""
WPI Profit Analyser
Author : 1st Year BTech Student
Data   : India Wholesale Price Index (2012-13 to 2022-23)

Libraries needed:
    pip install pandas matplotlib

How to run:
    python wpi_analyser.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ──────────────────────────────────────────────
#  STEP 1 : Load and prepare data
# ──────────────────────────────────────────────

YEARS = [
    "2012-13", "2013-14", "2014-15", "2015-16", "2016-17",
    "2017-18", "2018-19", "2019-20", "2020-21", "2021-22", "2022-23"
]

def load_data(filepath):
    """Read the CSV and return a clean DataFrame."""
    df = pd.read_csv(filepath)
    df.columns = ["Name", "Code", "Weight"] + [f"Idx_{y}" for y in YEARS]
    df["Name"]   = df["Name"].str.strip()
    df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")
    for y in YEARS:
        df[f"Idx_{y}"] = pd.to_numeric(df[f"Idx_{y}"], errors="coerce")
    return df


def analyse(df, base_year, compare_year):
    """
    Calculate:
      - % Change   = (compare - base) / base * 100
      - Profit/Loss signal
    """
    b = f"Idx_{base_year}"
    c = f"Idx_{compare_year}"

    result = df.copy()
    result["Base"]    = result[b]
    result["Compare"] = result[c]
    result["Change%"] = ((result["Compare"] - result["Base"]) / result["Base"] * 100).round(2)

    def signal(x):
        if x >= 5:
            return "SELL (Profit)"
        elif x >= 0:
            return "Hold"
        else:
            return "Avoid (Loss)"

    result["Signal"] = result["Change%"].apply(signal)
    result = result.dropna(subset=["Change%"])
    return result[["Name", "Weight", "Base", "Compare", "Change%", "Signal"]]


# ──────────────────────────────────────────────
#  STEP 2 : Main Window
# ──────────────────────────────────────────────

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("WPI Profit Analyser")
        self.geometry("1100x650")
        self.configure(bg="#f5f5f5")
        self.df_raw    = None   # original data
        self.df_result = None   # after analysis

        self._build_ui()

    # ── build the whole layout ──
    def _build_ui(self):

        # ── TOP BAR (title + file open) ──
        top = tk.Frame(self, bg="#1a1a2e", height=48)
        top.pack(fill="x")
        tk.Label(top, text="  WPI Profit Analyser",
                 bg="#1a1a2e", fg="white",
                 font=("Arial", 14, "bold")).pack(side="left", pady=10)
        tk.Button(top, text="Open CSV File",
                  command=self._open_file,
                  bg="#2a9d8f", fg="white",
                  font=("Arial", 10), relief="flat",
                  padx=10).pack(side="right", padx=14, pady=8)

        # ── CONTROL BAR (year pickers + buttons) ──
        ctrl = tk.Frame(self, bg="#e9ecef", pady=8)
        ctrl.pack(fill="x", padx=10)

        tk.Label(ctrl, text="Base Year:",
                 bg="#e9ecef", font=("Arial", 10)).pack(side="left", padx=(10, 4))
        self.var_base = tk.StringVar(value=YEARS[0])
        ttk.Combobox(ctrl, textvariable=self.var_base,
                     values=YEARS, state="readonly", width=10).pack(side="left")

        tk.Label(ctrl, text="   Compare Year:",
                 bg="#e9ecef", font=("Arial", 10)).pack(side="left", padx=(14, 4))
        self.var_cmp = tk.StringVar(value=YEARS[-1])
        ttk.Combobox(ctrl, textvariable=self.var_cmp,
                     values=YEARS, state="readonly", width=10).pack(side="left")

        tk.Label(ctrl, text="   Search:",
                 bg="#e9ecef", font=("Arial", 10)).pack(side="left", padx=(14, 4))
        self.var_search = tk.StringVar()
        tk.Entry(ctrl, textvariable=self.var_search,
                 width=18, font=("Arial", 10)).pack(side="left")

        tk.Button(ctrl, text="  Analyse  ",
                  command=self._run_analysis,
                  bg="#1a1a2e", fg="white",
                  font=("Arial", 10, "bold"), relief="flat",
                  padx=8).pack(side="left", padx=16)

        tk.Button(ctrl, text="Export CSV",
                  command=self._export,
                  bg="#555", fg="white",
                  font=("Arial", 10), relief="flat",
                  padx=8).pack(side="left")

        # ── KPI STRIP ──
        kpi_frame = tk.Frame(self, bg="#f5f5f5")
        kpi_frame.pack(fill="x", padx=10, pady=(6, 2))

        self.kpi_labels = {}
        kpi_defs = [
            ("total",  "Total Items",      "#1a1a2e"),
            ("profit", "Sell (Profit)",    "#2a9d8f"),
            ("hold",   "Hold",             "#c67a00"),
            ("loss",   "Avoid (Loss)",     "#e76f51"),
            ("avg",    "Avg % Change",     "#457b9d"),
        ]
        for key, label, color in kpi_defs:
            box = tk.Frame(kpi_frame, bg="white", bd=1,
                           relief="solid", padx=14, pady=8)
            box.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(box, text=label, bg="white",
                     fg="#555", font=("Arial", 8)).pack()
            val_lbl = tk.Label(box, text="—", bg="white",
                               fg=color, font=("Arial", 15, "bold"))
            val_lbl.pack()
            self.kpi_labels[key] = val_lbl

        # ── NOTEBOOK (tabs) ──
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=6)

        self.tab_table  = ttk.Frame(nb)
        self.tab_profit = ttk.Frame(nb)
        self.tab_loss   = ttk.Frame(nb)
        self.tab_chart  = ttk.Frame(nb)
        self.tab_graphs = ttk.Frame(nb)

        nb.add(self.tab_table,  text="  All Items  ")
        nb.add(self.tab_profit, text="  Best to Sell  ")
        nb.add(self.tab_loss,   text="  Avoid These  ")
        nb.add(self.tab_chart,  text="  Bar Chart  ")
        nb.add(self.tab_graphs, text="  Charts  ")

        self._build_table(self.tab_table)
        self._build_simple_table(self.tab_profit, "profit")
        self._build_simple_table(self.tab_loss,   "loss")
        self._build_chart_tab()
        self._build_graphs_tab()

        # ── STATUS BAR ──
        self.status = tk.Label(self, text="Open a CSV file to start.",
                               bg="#ddd", anchor="w",
                               font=("Arial", 9), padx=10)
        self.status.pack(fill="x", side="bottom")

    # ── TABLE (All Items) ──
    def _build_table(self, parent):
        cols = ("Name", "Weight", "Base Index", "Compare Index", "% Change", "Signal")
        widths = (280, 70, 100, 110, 90, 120)

        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=6, pady=6)

        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col,
                         command=lambda c=col: self._sort(c))
            tree.column(col, width=w,
                        anchor="w" if col == "Name" else "center")

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.tag_configure("profit", foreground="#2a9d8f")
        tree.tag_configure("hold",   foreground="#c67a00")
        tree.tag_configure("loss",   foreground="#e76f51")

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        tree.bind("<Double-1>", lambda e: self._show_detail(tree))
        self.tree_all = tree

    # ── SIMPLE TABLE (Profit / Loss tabs) ──
    def _build_simple_table(self, parent, kind):
        cols = ("#", "Name", "Weight", "% Change", "Signal")
        widths = (40, 320, 80, 100, 130)

        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=6, pady=6)

        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w,
                        anchor="w" if col == "Name" else "center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.tag_configure("profit", foreground="#2a9d8f")
        tree.tag_configure("hold",   foreground="#c67a00")
        tree.tag_configure("loss",   foreground="#e76f51")

        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        if kind == "profit":
            self.tree_profit = tree
        else:
            self.tree_loss = tree

    # ── GRAPHS TAB (Bar + Histogram + Box Plot + Line Graph) ──
    def _build_graphs_tab(self):
        parent = self.tab_graphs

        # Control row
        ctrl = tk.Frame(parent, bg="#e9ecef", pady=6)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="Top N:", bg="#e9ecef",
                 font=("Arial", 10)).pack(side="left", padx=(10, 4))
        self.var_gn = tk.IntVar(value=10)
        ttk.Combobox(ctrl, textvariable=self.var_gn,
                     values=[5, 10, 15, 20, 30],
                     state="readonly", width=5).pack(side="left")

        tk.Label(ctrl, text="   Graph:", bg="#e9ecef",
                 font=("Arial", 10)).pack(side="left", padx=(14, 4))
        self.var_gtype = tk.StringVar(value="Bar Graph")
        ttk.Combobox(ctrl, textvariable=self.var_gtype,
                     values=["Bar Graph", "Histogram", "Box Plot", "Line Graph"],
                     state="readonly", width=14).pack(side="left")

        tk.Label(ctrl, text="   Show:", bg="#e9ecef",
                 font=("Arial", 10)).pack(side="left", padx=(14, 4))
        self.var_gshow = tk.StringVar(value="Best Profit")
        ttk.Combobox(ctrl, textvariable=self.var_gshow,
                     values=["Best Profit", "Worst Loss", "Both"],
                     state="readonly", width=12).pack(side="left")

        tk.Label(ctrl, text="   Item (Line):", bg="#e9ecef",
                 font=("Arial", 10)).pack(side="left", padx=(14, 4))
        self.var_gitem = tk.StringVar()
        tk.Entry(ctrl, textvariable=self.var_gitem,
                 width=16, font=("Arial", 10)).pack(side="left")

        tk.Button(ctrl, text="  Draw  ",
                  command=self._draw_graphs,
                  bg="#1a1a2e", fg="white",
                  font=("Arial", 10, "bold"), relief="flat",
                  padx=8).pack(side="left", padx=14)

        # Canvas
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        self.fig_g = Figure(figsize=(10, 5), facecolor="#f5f5f5")
        self.ax_g  = self.fig_g.add_subplot(111)
        canvas_g   = FigureCanvasTkAgg(self.fig_g, master=parent)
        NavigationToolbar2Tk(canvas_g, parent)
        canvas_g.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=4)
        self.canvas_g = canvas_g

    # Draw dispatcher
    def _draw_graphs(self):
        if self.df_result is None:
            messagebox.showinfo("No Data", "Run Analyse first.")
            return
        gtype = self.var_gtype.get()
        if gtype == "Bar Graph":
            self._draw_g_bar()
        elif gtype == "Histogram":
            self._draw_g_hist()
        elif gtype == "Box Plot":
            self._draw_g_box()
        else:
            self._draw_g_line()

    # 1. BAR GRAPH — best/worst % change
    def _draw_g_bar(self):
        df   = self.df_result
        n    = self.var_gn.get()
        show = self.var_gshow.get()

        if show == "Best Profit":
            subset = df.nlargest(n, "Change%")
            colors = ["#2a9d8f"] * len(subset)
            title  = f"Top {n} Items — Best to SELL (Highest % Change)"
        elif show == "Worst Loss":
            subset = df.nsmallest(n, "Change%")
            colors = ["#e76f51"] * len(subset)
            title  = f"Top {n} Items — AVOID (Lowest % Change)"
        else:
            half = max(n // 2, 1)
            top  = df.nlargest(half, "Change%").assign(_c="#2a9d8f")
            bot  = df.nsmallest(half, "Change%").assign(_c="#e76f51")
            subset = pd.concat([top, bot])
            colors = list(subset["_c"])
            title  = f"Top {half} Profit vs Top {half} Loss"

        self.fig_g.clf()
        ax = self.fig_g.add_subplot(111)
        bars = ax.barh(range(len(subset)), subset["Change%"].values,
                       color=colors, edgecolor="white", height=0.65)
        ax.set_yticks(range(len(subset)))
        ax.set_yticklabels([nm[:38] for nm in subset["Name"]], fontsize=8)
        ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
        ax.set_xlabel("% Price Change")
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.invert_yaxis()
        for bar, val in zip(bars, subset["Change%"]):
            ax.text(bar.get_width() + (0.4 if val >= 0 else -0.4),
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:+.1f}%", va="center",
                    ha="left" if val >= 0 else "right", fontsize=7.5)
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(facecolor="#2a9d8f", label="Profit / Sell"),
                           Patch(facecolor="#e76f51", label="Loss / Avoid")],
                  fontsize=8)
        self.fig_g.tight_layout()
        self.canvas_g.draw()

    # 2. HISTOGRAM — distribution of % changes
    def _draw_g_hist(self):
        vals = self.df_result["Change%"].dropna()
        base = self.var_base.get()
        cmp  = self.var_cmp.get()

        self.fig_g.clf()
        ax = self.fig_g.add_subplot(111)
        ax.hist(vals, bins=40, color="#457b9d", edgecolor="white", alpha=0.85)
        ax.axvline(0,             color="red",    linewidth=1.5, linestyle="--",
                   label="0%  Break-even")
        ax.axvline(vals.mean(),   color="orange", linewidth=1.5, linestyle="--",
                   label=f"Mean  {vals.mean():+.1f}%")
        ax.axvline(vals.median(), color="green",  linewidth=1.5, linestyle="-.",
                   label=f"Median {vals.median():+.1f}%")
        ax.axvspan(0, vals.max(), alpha=0.05, color="green")
        ax.axvspan(vals.min(), 0, alpha=0.05, color="red")
        ax.set_xlabel("% Price Change")
        ax.set_ylabel("Number of Commodities")
        ax.set_title(f"Histogram — % Change Distribution  ({base} to {cmp})",
                     fontsize=11, fontweight="bold")
        ax.legend(fontsize=8)
        n_p = (vals > 0).sum()
        n_l = (vals < 0).sum()
        ax.text(0.98, 0.97,
                f"Profit items : {n_p}\nLoss items   : {n_l}\nTotal        : {len(vals)}",
                transform=ax.transAxes, va="top", ha="right", fontsize=9,
                bbox=dict(boxstyle="round", facecolor="white",
                          edgecolor="#ccc", alpha=0.9))
        self.fig_g.tight_layout()
        self.canvas_g.draw()

    # 3. BOX PLOT — index spread across all years
    def _draw_g_box(self):
        import matplotlib.cm as cm
        self.fig_g.clf()
        ax = self.fig_g.add_subplot(111)

        data = [self.df_raw[f"Idx_{y}"].dropna().values for y in YEARS]
        bp   = ax.boxplot(data, labels=YEARS, patch_artist=True,
                          showfliers=False,
                          medianprops=dict(color="black", linewidth=1.8),
                          whiskerprops=dict(linewidth=1),
                          capprops=dict(linewidth=1))
        cmap = cm.Blues
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(cmap(0.35 + 0.05 * i))
            patch.set_alpha(0.85)

        means = [self.df_raw[f"Idx_{y}"].mean() for y in YEARS]
        ax.plot(range(1, len(YEARS) + 1), means, "o--",
                color="red", linewidth=1.5, markersize=4, label="Mean index")
        ax.set_xlabel("Year")
        ax.set_ylabel("WPI Index Value")
        ax.set_title("Box Plot — WPI Index Spread Across All Years\n"
                     "(Box = 25th to 75th percentile of all commodities)",
                     fontsize=11, fontweight="bold")
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=35, ha="right", fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=8)
        self.fig_g.tight_layout()
        self.canvas_g.draw()

    # 4. LINE GRAPH — trend over years for selected items
    def _draw_g_line(self):
        query = self.var_gitem.get().strip().lower()
        n     = self.var_gn.get()

        if query:
            items = self.df_raw[
                self.df_raw["Name"].str.lower().str.contains(query, na=False)
            ].head(8)
        else:
            top_names = self.df_result.nlargest(n, "Change%")["Name"].tolist()
            items = self.df_raw[self.df_raw["Name"].isin(top_names)].head(n)

        self.fig_g.clf()
        ax = self.fig_g.add_subplot(111)

        if items.empty:
            ax.text(0.5, 0.5, "No matching items found.",
                    ha="center", va="center", transform=ax.transAxes)
            self.canvas_g.draw()
            return

        colors_list = ["#1a1a2e", "#2a9d8f", "#e76f51", "#457b9d",
                       "#c67a00", "#264653", "#6d6875", "#e9c46a"]
        for i, (_, row) in enumerate(items.iterrows()):
            vals = [row.get(f"Idx_{y}") for y in YEARS]
            clr  = colors_list[i % len(colors_list)]
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
                     fontsize=11, fontweight="bold")
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=35, ha="right", fontsize=8)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper left", ncol=2)
        self.fig_g.tight_layout()
        self.canvas_g.draw()

    # ── CHART TAB ──
    def _build_chart_tab(self):
        ctrl = tk.Frame(self.tab_chart, bg="#e9ecef", pady=6)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="Show Top N:",
                 bg="#e9ecef", font=("Arial", 10)).pack(side="left", padx=10)
        self.var_n = tk.IntVar(value=15)
        ttk.Combobox(ctrl, textvariable=self.var_n,
                     values=[10, 15, 20, 30], state="readonly",
                     width=6).pack(side="left")

        tk.Label(ctrl, text="   Chart Type:",
                 bg="#e9ecef", font=("Arial", 10)).pack(side="left", padx=10)
        self.var_chart = tk.StringVar(value="Top Profit")
        ttk.Combobox(ctrl, textvariable=self.var_chart,
                     values=["Top Profit", "Top Loss", "% Change Distribution"],
                     state="readonly", width=22).pack(side="left")

        tk.Button(ctrl, text="Draw Chart",
                  command=self._draw_chart,
                  bg="#1a1a2e", fg="white",
                  font=("Arial", 10), relief="flat",
                  padx=8).pack(side="left", padx=14)

        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.fig.patch.set_facecolor("#f5f5f5")
        canvas = FigureCanvasTkAgg(self.fig, master=self.tab_chart)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
        self.canvas = canvas

    # ──────────────────────────────────────────────
    #  ACTIONS
    # ──────────────────────────────────────────────

    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Select WPI CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            self.df_raw = load_data(path)
            self.status.configure(
                text=f"Loaded: {path}  |  Rows: {len(self.df_raw)}"
            )
            self._run_analysis()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{e}")

    def _run_analysis(self):
        if self.df_raw is None:
            messagebox.showinfo("No Data", "Please open a CSV file first.")
            return

        base = self.var_base.get()
        cmp  = self.var_cmp.get()

        # Validate years
        if YEARS.index(base) >= YEARS.index(cmp):
            messagebox.showwarning(
                "Year Error",
                "Compare year must be AFTER base year.\n"
                "Example: Base = 2012-13, Compare = 2022-23"
            )
            return

        df = analyse(self.df_raw, base, cmp)

        # Apply search filter
        q = self.var_search.get().strip().lower()
        if q:
            df = df[df["Name"].str.lower().str.contains(q, na=False)]

        # Sort by % Change descending
        df = df.sort_values("Change%", ascending=False).reset_index(drop=True)
        self.df_result = df

        self._update_kpis()
        self._fill_tables()
        self.status.configure(
            text=f"Analysis done  |  Base: {base}  ->  Compare: {cmp}  |  Items: {len(df)}"
        )

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

        # ── All Items ──
        self.tree_all.delete(*self.tree_all.get_children())
        for _, row in df.iterrows():
            tag = ("profit" if row["Signal"] == "SELL (Profit)"
                   else "loss" if row["Signal"] == "Avoid (Loss)"
                   else "hold")
            self.tree_all.insert("", "end", tags=(tag,), values=(
                row["Name"][:55],
                f"{row['Weight']:.4f}",
                f"{row['Base']:.1f}"    if pd.notna(row["Base"])    else "—",
                f"{row['Compare']:.1f}" if pd.notna(row["Compare"]) else "—",
                f"{row['Change%']:+.2f}%",
                row["Signal"],
            ))

        # ── Best to Sell (top 50 by % change, positive only) ──
        top = df[df["Change%"] > 0].head(50).reset_index(drop=True)
        self.tree_profit.delete(*self.tree_profit.get_children())
        for i, row in top.iterrows():
            self.tree_profit.insert("", "end", tags=("profit",), values=(
                i + 1, row["Name"][:55],
                f"{row['Weight']:.4f}",
                f"{row['Change%']:+.2f}%",
                row["Signal"],
            ))

        # ── Avoid These (bottom 50 by % change) ──
        bot = df.tail(50).reset_index(drop=True)
        self.tree_loss.delete(*self.tree_loss.get_children())
        for i, row in bot.iterrows():
            tag = ("loss" if row["Signal"] == "Avoid (Loss)" else "hold")
            self.tree_loss.insert("", "end", tags=(tag,), values=(
                i + 1, row["Name"][:55],
                f"{row['Weight']:.4f}",
                f"{row['Change%']:+.2f}%",
                row["Signal"],
            ))

    def _draw_chart(self):
        if self.df_result is None:
            messagebox.showinfo("No Data", "Run Analyse first.")
            return

        df   = self.df_result
        n    = self.var_n.get()
        kind = self.var_chart.get()

        self.ax.clear()

        if kind == "% Change Distribution":
            vals = df["Change%"].dropna()
            self.ax.hist(vals, bins=35, color="#457b9d",
                         edgecolor="white", alpha=0.85)
            self.ax.axvline(0, color="red",    linestyle="--",
                            linewidth=1.2, label="Break-even (0%)")
            self.ax.axvline(vals.mean(), color="orange", linestyle="--",
                            linewidth=1.2, label=f"Mean ({vals.mean():+.1f}%)")
            self.ax.set_xlabel("% Price Change")
            self.ax.set_ylabel("Number of Commodities")
            self.ax.set_title("Distribution of % Price Changes")
            self.ax.legend()

        elif kind == "Top Loss":
            subset = df.nsmallest(n, "Change%")
            bars = self.ax.barh(range(len(subset)),
                                subset["Change%"].values,
                                color="#e76f51", edgecolor="white")
            self.ax.set_yticks(range(len(subset)))
            self.ax.set_yticklabels(
                [name[:35] for name in subset["Name"]], fontsize=8)
            self.ax.axvline(0, color="gray", linewidth=0.8)
            self.ax.set_xlabel("% Change")
            self.ax.set_title(f"Top {n} Items to AVOID (Lowest % Change)")
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
                                color="#2a9d8f", edgecolor="white")
            self.ax.set_yticks(range(len(subset)))
            self.ax.set_yticklabels(
                [name[:35] for name in subset["Name"]], fontsize=8)
            self.ax.axvline(0, color="gray", linewidth=0.8)
            self.ax.set_xlabel("% Change")
            self.ax.set_title(f"Top {n} Items to SELL (Highest % Change)")
            self.ax.invert_yaxis()
            for bar, val in zip(bars, subset["Change%"]):
                self.ax.text(bar.get_width() + 0.3,
                             bar.get_y() + bar.get_height() / 2,
                             f"{val:+.1f}%", va="center",
                             ha="left", fontsize=8)

        self.fig.tight_layout()
        self.canvas.draw()

    def _sort(self, col):
        """Sort the All Items table when a column header is clicked."""
        if self.df_result is None:
            return
        col_map = {
            "Name": "Name", "Weight": "Weight",
            "Base Index": "Base", "Compare Index": "Compare",
            "% Change": "Change%", "Signal": "Signal",
        }
        key = col_map.get(col, "Change%")
        asc = (key in ("Name", "Signal"))
        self.df_result = self.df_result.sort_values(
            key, ascending=asc).reset_index(drop=True)
        self._fill_tables()

    def _show_detail(self, tree):
        """Double-click a row to see a mini trend chart."""
        sel = tree.selection()
        if not sel:
            return
        name = tree.item(sel[0], "values")[0]
        row_match = self.df_raw[self.df_raw["Name"].str.startswith(name[:20])]
        if row_match.empty:
            return
        row = row_match.iloc[0]

        vals = [row.get(f"Idx_{y}", None) for y in YEARS]
        yrs  = [y for y, v in zip(YEARS, vals) if pd.notna(v)]
        vals = [v for v in vals if pd.notna(v)]

        win = tk.Toplevel(self)
        win.title(f"Trend — {name[:50]}")
        win.geometry("650x400")
        win.configure(bg="#f5f5f5")

        tk.Label(win, text=name, bg="#f5f5f5",
                 font=("Arial", 11, "bold"),
                 wraplength=620, justify="left").pack(padx=16, pady=(12, 4),
                                                      anchor="w")

        fig2, ax2 = plt.subplots(figsize=(8, 4))
        fig2.patch.set_facecolor("#f5f5f5")
        ax2.plot(yrs, vals, marker="o", color="#1a1a2e",
                 linewidth=2, markersize=5)
        ax2.fill_between(range(len(vals)), vals, alpha=0.1, color="#2a9d8f")
        ax2.set_xticks(range(len(yrs)))
        ax2.set_xticklabels(yrs, rotation=35, ha="right", fontsize=8)
        ax2.set_ylabel("WPI Index")
        ax2.set_title("Historical WPI Index")
        ax2.grid(True, alpha=0.3)
        fig2.tight_layout()

        c2 = FigureCanvasTkAgg(fig2, master=win)
        c2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=6)

    def _export(self):
        if self.df_result is None:
            messagebox.showinfo("No Data", "Run Analyse first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="wpi_analysis_result.csv"
        )
        if path:
            self.df_result.to_csv(path, index=False)
            messagebox.showinfo("Saved", f"File saved to:\n{path}")


# ──────────────────────────────────────────────
#  STEP 3 : Run the app
# ──────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
