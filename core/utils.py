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

def dbm_to_color(dbm):
    if dbm == "N/A" or dbm is None:
        return "red"
    
    try:
        dbm_val = float(dbm)
        if dbm_val >= -30:  # -30 ou melhor = Verde (excelente)
            return "green"
        elif dbm_val >= -49:  # -30 a -49 = Amarelo (bom)  
            return "orange"
        elif dbm_val >= -60:  # -50 a -60 = Vermelho (ruim)
            return "red"
        else:  # Pior que -60 = Vermelho escuro (muito ruim)
            return "red"
    except:
        return "red"