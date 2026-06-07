import tkinter as tk
from tkinter import ttk
from core.session_manager import get_season_gp_list

# --- Theme Colors ---
BG          = "#0f0f0f"
CARD_BG     = "#1a1a1a"
ACCENT      = "#e10600"   # F1 red
TEXT        = "#ffffff"
SUBTEXT     = "#aaaaaa"
INPUT_BG    = "#2a2a2a"
INPUT_FG    = "#ffffff"
HOVER_BTN   = "#c00500"

def get_race_selection():
    result = {"year": None, "gp": None}

    root = tk.Tk()
    root.title("F1 Race Replay")
    root.geometry("400x320")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.configure(bg=BG)

    # --- Style ---
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TCombobox",
        fieldbackground=INPUT_BG,
        background=INPUT_BG,
        foreground=INPUT_FG,
        arrowcolor=ACCENT,
        bordercolor="#333333",
        lightcolor="#333333",
        darkcolor="#333333",
        selectbackground=ACCENT,
        selectforeground=TEXT,
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", INPUT_BG)],
        foreground=[("readonly", INPUT_FG)],
    )

    # --- Header ---
    header = tk.Frame(root, bg=ACCENT, height=50)
    header.pack(fill="x")
    tk.Label(
        header, text="🏎  F1 RACE REPLAY", 
        bg=ACCENT, fg=TEXT,
        font=("Arial", 14, "bold"),
        pady=12
    ).pack()

    # --- Card ---
    card = tk.Frame(root, bg=CARD_BG, padx=30, pady=20)
    card.pack(fill="both", expand=True, padx=20, pady=15)

    # Year row
    tk.Label(card, text="SEASON", bg=CARD_BG, fg=SUBTEXT,
             font=("Arial", 8, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 3))
    year_var = tk.StringVar(value="2025")
    year_box = ttk.Combobox(card, textvariable=year_var,
                             values=list(range(2019, 2026)),
                             width=25, state="readonly", font=("Arial", 11))
    year_box.grid(row=1, column=0, sticky="ew", pady=(0, 15))

    # GP row
    tk.Label(card, text="GRAND PRIX", bg=CARD_BG, fg=SUBTEXT,
             font=("Arial", 8, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 3))
    gp_var = tk.StringVar()
    gp_box = ttk.Combobox(card, textvariable=gp_var,
                           width=25, state="readonly", font=("Arial", 11))
    gp_box.grid(row=3, column=0, sticky="ew", pady=(0, 20))

    card.columnconfigure(0, weight=1)

    def load_gps(event=None):
        gp_list = get_season_gp_list(int(year_var.get()))
        gp_box["values"] = gp_list
        if gp_list:
            gp_var.set(gp_list[0])

    year_box.bind("<<ComboboxSelected>>", load_gps)
    load_gps()

    # Button
    def confirm():
        result["year"] = int(year_var.get())
        result["gp"]   = gp_box.get()  # use gp_box.get() directly, not gp_var.get()
        root.destroy()

    btn = tk.Button(
        card, text="START REPLAY ▶",
        bg=ACCENT, fg=TEXT,
        font=("Arial", 11, "bold"),
        relief="flat", cursor="hand2",
        activebackground=HOVER_BTN,
        activeforeground=TEXT,
        pady=8,
        command=confirm
    )
    btn.grid(row=4, column=0, sticky="ew")

    root.mainloop()
    return result["year"], result["gp"]