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
        return "gray"
    
    try:
        dbm_val = float(dbm)
        
        # Arredondar para o nível mais próximo (múltiplo de 10)
        rounded_dbm = round(dbm_val / 10) * 10
        
        # Mapeamento exato baseado no valor arredondado
        if rounded_dbm >= -30:
            return "#00FFFF"  # -30: Verde azulado/Ciano
        elif rounded_dbm >= -40:
            return "#90EE90"  # -40: Verde claro
        elif rounded_dbm >= -50:
            return "#ADFF2F"  # -50: Amarelo esverdeado
        elif rounded_dbm >= -60:
            return "#FFA500"  # -60: Laranja
        elif rounded_dbm >= -70:
            return "#FF4500"  # -70: Laranja avermelhado
        else:  # -80 ou pior
            return "#FF0000"  # -80: Vermelho
    except:
        return "gray"