import tkinter as tk
from tkinter import ttk, Frame, Button, Label, Entry
from portfolio import enrich_portfolio, add_holding, remove_holding
from models import  get_client
from util.util import currency_symbol, fmt_money, fmt_percent
from util.util import normalize_symbol
from matplotlib.dates import AutoDateLocator, DateFormatter


from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


class FinanceDashboard:
    def __init__(self, root):
        self.root = root
        self.api_client = get_client()
        self._after_id = None

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._build_tabs()

        quit_btn = tk.Button(self.root, text="Quit", command=self.close)
        quit_btn.pack(pady=10)


    def _refresh_data(self):
        symbol = self.entry.get().strip() or "BTC"
        try:
            quote = self.api_client.get_quote(symbol)
            self.label.config(text=f"{quote.symbol} | Price: ${quote.price:.2f}")
        except Exception as e:
            self.label.config(text=f"Error: {e}")

        # Schedule next refresh
        self._after_id = self.root.after(5000, self._refresh_data)

    def _build_tabs(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        market_tab = Frame(notebook)
        MarketDataUI(market_tab, self.api_client)
        notebook.add(market_tab, text="Market Data")

        portfolio_tab = Frame(notebook)
        PortfolioUI(portfolio_tab, self.api_client)
        notebook.add(portfolio_tab, text="Portfolio")



    def close(self):
        # Cancel any scheduled tasks
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)

        # Destroy chart canvases if any
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Widget):
                widget.destroy()

        # Close matplotlib figures
        import matplotlib.pyplot as plt
        plt.close("all")

        # Finally destroy root
        self.root.quit()
        self.root.destroy()




class PortfolioUI:
    def __init__(self, parent, api_client):
        self.parent = parent
        self.api_client = api_client
        self.tree = None
        self.symbol_entry = None
        self.qty_entry = None
        self.price_entry = None
        self._build_ui()
        self._refresh_data()

    def _build_ui(self):
        control_frame = Frame(self.parent)
        control_frame.pack(fill="x", pady=5)

        Label(control_frame, text="Symbol").pack(side="left")
        self.symbol_entry = Entry(control_frame, width=10)
        self.symbol_entry.pack(side="left", padx=5)

        Label(control_frame, text="Qty").pack(side="left")
        self.qty_entry = Entry(control_frame, width=8)
        self.qty_entry.pack(side="left", padx=5)

        Label(control_frame, text="Buy Price").pack(side="left")
        self.price_entry = Entry(control_frame, width=8)
        self.price_entry.pack(side="left", padx=5)

        Button(control_frame, text="Add", command=self._add).pack(side="left", padx=5)
        Button(control_frame, text="Remove", command=self._remove).pack(side="left", padx=5)
        Button(control_frame, text="Refresh", command=self._refresh_data).pack(side="left", padx=5)

        columns = (
            "Symbol", "Quantity", "Buy Price", "Current Price",
            "Value", "P/L", "P/L %", "Source"
        )
        self.tree = ttk.Treeview(self.parent, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)

    def _add(self):
        sym = self.symbol_entry.get().strip()
        qty = float(self.qty_entry.get() or 0)
        bp = float(self.price_entry.get() or 0)
        if sym and qty > 0:
            add_holding(sym, qty, bp)
            self._refresh_data()

    def _remove(self):
        # Prefer selected row; fallback to entry box
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            values = self.tree.item(item_id, "values")
            sym = values[0] if values else ""
        else:
            sym = self.symbol_entry.get().strip()

        if not sym:
            return

        remove_holding(sym)
        self._refresh_data()

    def _refresh_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        enriched = enrich_portfolio(self.api_client)
        for h in enriched:
            pl = h["pl"]
            color = "green" if pl > 0 else "red" if pl < 0 else "black"
            self.tree.insert(
                "",
                "end",
                values=(
                    h["symbol"],
                    h["quantity"],
                    fmt_money(h["buy_price"]),
                    fmt_money(h["current_price"]),
                    fmt_money(h["value"]),
                    fmt_money(h["pl"]),
                    fmt_percent(h["pl_percent"]),
                    h["source"],
                ),
                tags=(color,)
            )

        self.tree.tag_configure("green", foreground="green")
        self.tree.tag_configure("red", foreground="red")
        self.tree.tag_configure("black", foreground="black")


class MarketDataUI:
    def __init__(self, parent, api_client):
        self.parent = parent
        self.api_client = api_client
        self.symbol = "BTC-USD"
        self.range = "1mo"
        self.label = None
        self.chart_canvas = None
        self._build_ui()
        self._refresh_data()

    def _build_ui(self):
        control_frame = Frame(self.parent)
        control_frame.pack(fill="x", pady=5)

        Label(control_frame, text="Symbol").pack(side="left")
        self.entry = Entry(control_frame, width=12)
        self.entry.insert(0, self.symbol)
        self.entry.pack(side="left", padx=5)

        Button(control_frame, text="Load & Update Chart",
               command=self._load_and_update).pack(side="left", padx=5)

        Label(control_frame, text="Range").pack(side="left", padx=10)
        self.range_var = tk.StringVar(value=self.range)
        range_menu = ttk.Combobox(
            control_frame,
            textvariable=self.range_var,
            values=["1mo", "6mo", "1y", "5y", "10y", "max"]
        )
        range_menu.pack(side="left")

        self.label = Label(self.parent, text="Loading...")
        self.label.pack(anchor="w", padx=10, pady=5)

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.set_title("Market Chart")
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.parent)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _load_and_update(self):
        raw = self.entry.get().strip()
        if raw:
            self.symbol = normalize_symbol(raw)  
        self._refresh_data()


    def _refresh_data(self):
        try:
            quote = self.api_client.get_quote(self.symbol)
            text = f"{quote.symbol} | Price: {currency_symbol(self.symbol)}{fmt_money(quote.price)}"
            self.label.config(text=text)

            series = self.api_client.get_daily(self.symbol, self.range_var.get())
            xs = [p.time for p in series.points]
            ys = [p.close for p in series.points]

            ax = self.chart_canvas.figure.axes[0]
            ax.clear()
            ax.set_title(f"{self.symbol} ({self.range_var.get()})")
            ax.plot(xs, ys, linewidth=2, color="blue")
            ax.set_xlabel("Date")
            ax.set_ylabel("Price")
            ax.grid(True)

            # Format x-axis dates
            ax.xaxis.set_major_locator(AutoDateLocator())
            ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
            self.chart_canvas.figure.autofmt_xdate()

            self.chart_canvas.draw()

        except Exception as e:
            self.label.config(text=f"{self.symbol}: error {e}")
            ax = self.chart_canvas.figure.axes[0]
            ax.clear()
            ax.set_title(f"{self.symbol} ({self.range_var.get()})")
            ax.text(0.5, 0.5, f"No data available for {self.symbol}",
                    ha="center", va="center", transform=ax.transAxes)
            ax.grid(False)
            self.chart_canvas.draw()
