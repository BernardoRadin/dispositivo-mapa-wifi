import tkinter as tk
from gui.wifi_app import WifiMapApp

def main():
    """Função principal"""
    try:
        import matplotlib
        matplotlib.use('TkAgg')
    except ImportError:
        print("Aviso: matplotlib não encontrado. Instale com: pip install matplotlib")
    
    root = tk.Tk()
    app = WifiMapApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()