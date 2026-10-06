"""
Versión para GitHub Actions: revisa UNA vez y termina.
Guarda el estado en estado.json (el workflow lo sube al repo).
"""
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

TCL_JS = "https://tclstore.cl/products/monitor-gamer-tcl-mini-led-27p2a-pro-qhd-320hz.js"
TCL_URL = "https://tclstore.cl/products/monitor-gamer-tcl-mini-led-27p2a-pro-qhd-320hz"
SOLOTODO_URL = "https://www.solotodo.cl/products/397418-tcl-27p2a-pro"

ESTADO = Path(__file__).with_name("estado.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (monitor personal de stock)"}

TG_TOKEN = "".join(os.environ["TG_TOKEN"].split())
TG_CHAT_ID = "".join(os.environ["TG_CHAT_ID"].split())


def avisar(texto: str) -> None:
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id": TG_CHAT_ID, "text": texto},
        timeout=15,
    )
    print("Telegram:", "enviado" if r.ok else f"ERROR {r.status_code} {r.text}")


def tcl_disponible() -> bool:
    r = requests.get(TCL_JS, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return bool(r.json().get("available"))


def tiendas_solotodo() -> set[str]:
    r = requests.get(SOLOTODO_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    ignorar = ("solotodo", "facebook", "google", "twitter", "instagram",
               "youtube", "gstatic", "doubleclick", "cloudflare")
    dominios = set()
    for url in re.findall(r'<a\s[^>]*href="(https?://[^"]+)"', r.text):
        host = urlparse(url).netloc.replace("www.", "")
        if host and not any(x in host for x in ignorar):
            dominios.add(host)
    return dominios


def main() -> None:
    e = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}

    # 1) TCL Store
    try:
        hay = tcl_disponible()
        if hay and not e.get("tcl"):
            avisar(f"✅ ¡HAY STOCK en TCL Store!\n{TCL_URL}")
        e["tcl"] = hay
    except Exception as ex:
        print("Error TCL:", ex)

    # 2) SoloTodo: tiendas nuevas
    try:
        actuales = tiendas_solotodo()
        previas = set(e.get("tiendas", []))
        if previas:
            nuevas = actuales - previas
            if nuevas:
                avisar("🛒 Nueva tienda en SoloTodo: " + ", ".join(sorted(nuevas))
                       + f"\n{SOLOTODO_URL}")
        e["tiendas"] = sorted(actuales | previas)
    except Exception as ex:
        print("Error SoloTodo:", ex)

    ESTADO.write_text(json.dumps(e, indent=2))
    print(e)


if __name__ == "__main__":
    main()
