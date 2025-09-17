import threading
import time
import pywifi
from pywifi import PyWiFi
import tkinter as tk
from tkinter import ttk

SSID_TARGET = ".URI-C2"
SCAN_INTERVAL = 2000  # ms

def signal_dbm_to_percent(dbm):
    try:
        val = float(dbm)
    except Exception:
        return 0
    if val <= -100:
        return 0
    if val >= -50:
        return 100
    return max(0, min(100, int(round(2 * (val + 100)))))

def signal_to_color(pct):
    if pct <= 33:
        return "red"
    elif pct <= 66:
        return "orange"
    else:
        return "green"

class WifiScanner:
    def __init__(self):
        self.wifi = PyWiFi()
        self.iface = self.wifi.interfaces()[0] if self.wifi.interfaces() else None
        self.lock = threading.Lock()

    def scan_once(self):
        if self.iface is None:
            return None
        try:
            self.iface.scan()
            time.sleep(1.0)
            raw = self.iface.scan_results()
        except Exception:
            return None

        best_signal = None
        for r in raw:
            if r.ssid == SSID_TARGET:
                sig = getattr(r, 'signal', None)
                if sig is not None and (best_signal is None or sig > best_signal):
                    best_signal = sig
        return best_signal

class WifiMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mapa de Sinal Wi-Fi")
        self.root.geometry("500x400")
        self.scanner = WifiScanner()
        self.create_widgets()

        self.measurements = []  # lista de medidas

    def create_widgets(self):
        frame_top = ttk.Frame(self.root, padding=8)
        frame_top.pack(fill='x')

        ttk.Label(frame_top, text="Local:").pack(side='left')
        self.combo_local = ttk.Combobox(frame_top, state='readonly', values=["Banheiro", "Sala", "Corredor"])
        self.combo_local.current(0)
        self.combo_local.pack(side='left', padx=8)

        self.btn_measure = ttk.Button(frame_top, text="Medir", command=self.on_measure)
        self.btn_measure.pack(side='left', padx=8)

        # frame histórico
        self.frame_list = ttk.Frame(self.root, padding=8)
        self.frame_list.pack(fill='both', expand=True)

        self.tree = ttk.Treeview(self.frame_list, columns=("local","dbm","percent"), show='headings')
        self.tree.heading("local", text="Local")
        self.tree.heading("dbm", text="Sinal (dBm)")
        self.tree.heading("percent", text="%")
        self.tree.column("local", width=120, anchor='w')
        self.tree.column("dbm", width=100, anchor='center')
        self.tree.column("percent", width=80, anchor='center')
        self.tree.pack(fill='both', expand=True)

    def on_measure(self):
        local = self.combo_local.get()
        self.btn_measure.config(state='disabled')
        self.root.update()

        # faz scan
        sig = self.scanner.scan_once()
        if sig is None:
            dbm_str = "N/A"
            pct = 0
        else:
            dbm_str = f"{sig} dBm"
            pct = signal_dbm_to_percent(sig)

        color = signal_to_color(pct)

        # salva medida
        self.measurements.append((local, dbm_str, f"{pct}%", color))

        # atualiza treeview
        self.tree.insert('', 'end', values=(local, dbm_str, f"{pct}%"), tags=(color,))
        self.tree.tag_configure("red", background="#ffcccc")
        self.tree.tag_configure("orange", background="#ffedcc")
        self.tree.tag_configure("green", background="#ccffcc")

        self.btn_measure.config(state='normal')

def main():
    root = tk.Tk()
    app = WifiMapApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
