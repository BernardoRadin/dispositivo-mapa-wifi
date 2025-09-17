import time
import pywifi
from pywifi import PyWiFi

class WifiScanner:
    def __init__(self):
        self.wifi = PyWiFi()
        self.iface = self.wifi.interfaces()[0] if self.wifi.interfaces() else None

    def scan_once(self, target_ssid):
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
            if r.ssid == target_ssid:
                sig = getattr(r, 'signal', None)
                if sig is not None and (best_signal is None or sig > best_signal):
                    best_signal = sig
        return best_signal

    def scan_networks(self):
        if self.iface is None:
            return []
            
        try:
            self.iface.scan()
            time.sleep(2.0)  # Aguarda o scan terminar
            redes = self.iface.scan_results()
            
            lista_ssids = []
            for r in redes:
                if r.ssid and r.ssid not in lista_ssids:
                    lista_ssids.append(r.ssid)
            
            return lista_ssids
        except Exception:
            return []