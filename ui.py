# src/ui.py

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from api import YahooFinanceClient
from portfolio import enrich_portfolio, add_holding, remove_holding
from utils.util import normalize_symbol, percent_str


class FinanceDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Finance Dashboard")
        self.geometry("1100x750")

        self.api = YahooFinanceClient()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self._build_market_data_tab()
        self._build_portfolio_tab()

        # ✅ Quit button at bottom
        ttk.Button(self, text="Quit", command=self._quit_app).pack(pady=6)

    def _quit_app(self):
        """Cleanly exit the application."""
        self.quit()     # stop Tkinter mainloop
        self.destroy()  # close the window

    # ---------------- Market Data Tab ----------------
    def _build_market_data_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Market Data")

        ttk.Label(frame, text="Symbol or pair (e.g., BTC, AAPL, USD-EUR):").grid(
            row=0, column=0, sticky="w", padx=8, pady=6
        )

        common_symbols = [
            "AAPL", "MSFT", "NVDA",          # Stocks
            "BTC", "ETH", "DOGE", "SOL",     # Crypto shorthand
            "EUR-USD", "RON-USD", "USD-JPY", # Forex pairs
        ]

        self.market_symbol = tk.StringVar(value="BTC")
        self.symbol_dropdown = ttk.Combobox(
            frame,
            textvariable=self.market_symbol,
            values=common_symbols,
            width=20
        )
        self.symbol_dropdown.grid(row=0, column=1, sticky="w", padx=8, pady=6)

        # Buttons and chart range selector
        btns = ttk.Frame(frame)
        btns.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=6)
        ttk.Button(btns, text="Get quote", command=self._refresh_market_quote).pack(side="left", padx=4)

        self.chart_range = tk.StringVar(value="1mo")
        ranges = [
            ("1 Month", "1mo"),
            ("1 Year", "1y"),
            ("5 Years", "5y"),
            ("Max", "max")   # ✅ new option
        ]
        for label, val in ranges:
            ttk.Radiobutton(btns, text=label, variable=self.chart_range, value=val).pack(side="left", padx=4)

        ttk.Button(btns, text="Load chart", command=self._load_market_chart).pack(side="left", padx=4)

        # Quote text
        self.market_text = tk.StringVar()
        ttk.Label(frame, textvariable=self.market_text, anchor="w", justify="left").grid(
            row=2, column=0, columnspan=2, sticky="we", padx=8, pady=6
        )

        # Chart
        self.market_fig, self.market_ax = plt.subplots(figsize=(8.5, 5))
        self.market_canvas = FigureCanvasTkAgg(self.market_fig, master=frame)
        self.market_canvas.get_tk_widget().grid(row=3, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)

        frame.grid_rowconfigure(3, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def _refresh_market_quote(self):
        raw_symbol = self.market_symbol.get()
        symbol = normalize_symbol(raw_symbol)  # ✅ always normalize
        try:
            quote = self.api.get_quote(symbol)
            self.market_text.set(
                f"Symbol: {quote.symbol}\n"
                f"Price: ${quote.price:.2f}\n"
                f"Change: {quote.change:.2f} ({percent_str(quote.change_percent)})\n"
                f"Source: {quote.source}"
            )
        except Exception as e:
            self.market_text.set(f"Symbol: {symbol}\nNo data available.\nError: {e}")

    def _load_market_chart(self):
        raw_symbol = self.market_symbol.get()
        symbol = normalize_symbol(raw_symbol)  # ✅ always normalize
        period = self.chart_range.get()
        series = self.api.get_daily(symbol, period=period)
        self.market_ax.clear()
        if series.points:
            times = [p.time for p in series.points]
            closes = [p.close for p in series.points]
            self.market_ax.plot(times, closes, label=f"{symbol} ({period})")
            self.market_ax.set_title(f"{symbol} - {period} Chart")
            self.market_ax.legend()
        else:
            self.market_ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        self.market_canvas.draw()

    # ---------------- Portfolio Tab ----------------
    def _build_portfolio_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Portfolio")

        columns = ("symbol", "quantity", "buy_price", "total_spent",
                   "current_price", "value", "pl", "pl_percent", "currency", "source")
        self.portfolio_tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.portfolio_tree.heading(col, text=col.capitalize())
        self.portfolio_tree.pack(fill="both", expand=True, padx=8, pady=8)

        btns = ttk.Frame(frame)
        btns.pack(fill="x", padx=8, pady=6)
        ttk.Button(btns, text="Refresh", command=self._refresh_portfolio).pack(side="left", padx=4)
        ttk.Button(btns, text="Add holding", command=self._add_holding).pack(side="left", padx=4)
        ttk.Button(btns, text="Remove holding", command=self._remove_holding).pack(side="left", padx=4)

        self._refresh_portfolio()

    def _refresh_portfolio(self):
        for row in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(row)

        enriched = enrich_portfolio(self.api)
        for h in enriched:
            values = (
                h["symbol"], h["quantity"], f"${h['buy_price']:.2f}", f"${h['total_spent']:.2f}",
                f"${h['current_price']:.2f}" if h["current_price"] else "N/A",
                f"${h['value']:.2f}" if h["value"] else "N/A",
                f"${h['pl']:.2f}", percent_str(h["pl_percent"]),
                h["currency"], h["source"]
            )
            tag = "profit" if h["pl"] >= 0 else "loss"
            self.portfolio_tree.insert("", "end", values=values, tags=(tag,))

        self.portfolio_tree.tag_configure("profit", background="#d4edda")
        self.portfolio_tree.tag_configure("loss", background="#f8d7da")

    def _add_holding(self):
        top = tk.Toplevel(self)
        top.title("Add Holding")

        ttk.Label(top, text="Symbol:").grid(row=0, column=0, padx=6, pady=6)
        sym_var = tk.StringVar()
        ttk.Entry(top, textvariable=sym_var).grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(top, text="Quantity:").grid(row=1, column=0, padx=6, pady=6)
        qty_var = tk.DoubleVar()
        ttk.Entry(top, textvariable=qty_var).grid(row=1, column=1, padx=6, pady=6)

        ttk.Label(top, text="Buy Price:").grid(row=2, column=0, padx=6, pady=6)
        buy_var = tk.DoubleVar()
        ttk.Entry(top, textvariable=buy_var).grid(row=2, column=1, padx=6, pady=6)

        def save():
            add_holding(normalize_symbol(sym_var.get()), qty_var.get(), buy_var.get())
            self._refresh_portfolio()
            top.destroy()

        ttk.Button(top, text="Save", command=save).grid(row=3, column=0, columnspan=2, pady=8)

    def _remove_holding(self):
        selected = self.portfolio_tree.selection()
        if not selected:
            return
        try:
            symbol = self.portfolio_tree.item(selected[0])["values"][0]
            remove_holding(symbol)
        except Exception as e:
            print(f"Error removing holding: {e}")
        finally:
            # ✅ Always refresh safely
            self._refresh_portfolio()