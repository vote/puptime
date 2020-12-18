
def psite(s):
    return f"Site({s['uuid']} {s['url']})"

def pproxy(p):
    return f"Proxy({p['uuid']} {p['address']})"

def pcheck(c):
    return f"Check({c['uuid']})"
