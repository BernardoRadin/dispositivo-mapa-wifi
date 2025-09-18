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
        rounded_dbm = round(dbm_val / 10) * 10
        
        if rounded_dbm >= -30:
            return "#00FFFF"
        elif rounded_dbm >= -40:
            return "#90EE90"
        elif rounded_dbm >= -50:
            return "#ADFF2F"
        elif rounded_dbm >= -60:
            return "#FFA500"
        elif rounded_dbm >= -70:
            return "#FF4500"
        else:
            return "#FF0000"
    except:
        return "gray"