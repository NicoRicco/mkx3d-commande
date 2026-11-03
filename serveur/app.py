"""Serveur web de commande du bras MKX3D.

Lancement :  python serveur/app.py            (puis ouvrir http://localhost:8080)
Options   :  --port-web 8080  --hote 0.0.0.0  --serie COM3 | /dev/ttyACM0 | simulateur
"""

import argparse
import asyncio
import json
import re
import socket
from pathlib import Path

from aiohttp import WSMsgType, web

from liaison import lister_ports
from robot import ErreurCommande, Robot

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_WEB = RACINE / "web"
DOSSIER_TRAJ = RACINE / "trajectoires"

clients = set()


def diffuser(message):
    texte = json.dumps(message)
    for ws in list(clients):
        if not ws.closed:
            asyncio.ensure_future(ws.send_str(texte))


robot = None


async def traiter(ws, msg):
    t = msg.get("type")
    if t == "ports":
        await ws.send_json({"type": "ports", "ports": lister_ports()})
    elif t == "connecter":
        await robot.connecter(msg.get("port") or "simulateur")
    elif t == "deconnecter":
        await robot.deconnecter()
    elif t == "deplacer":
        robot.deplacer(msg["q"], msg.get("duree"))
    elif t == "pince":
        robot.regler_pince(msg["valeur"])
    elif t == "stop":
        await robot.arreter()
    elif t == "definir_position":
        robot.definir_position(msg["q"])
    elif t == "lire":
        robot.lancer_lecture(msg["points"], bool(msg.get("boucle")))
    elif t == "arreter_lecture":
        await robot.arreter_lecture()
    else:
        raise ErreurCommande(f"Commande inconnue : {t}")


async def route_ws(request):
    ws = web.WebSocketResponse(heartbeat=10)
    await ws.prepare(request)
    clients.add(ws)
    await ws.send_json(robot.etat())
    for entree in robot.journal[-50:]:
        await ws.send_json(entree)
    try:
        async for m in ws:
            if m.type != WSMsgType.TEXT:
                continue
            try:
                await traiter(ws, json.loads(m.data))
            except (ErreurCommande, KeyError, ValueError, TypeError, OSError) as e:
                await ws.send_json({"type": "erreur", "message": str(e) or e.__class__.__name__})
    finally:
        clients.discard(ws)
    return ws


# ---------- trajectoires enregistrées (fichiers JSON) ----------

def nom_fichier(nom):
    propre = re.sub(r"[^\w\- ]", "", nom).strip()[:60]
    if not propre:
        raise web.HTTPBadRequest(text="Nom invalide")
    return DOSSIER_TRAJ / f"{propre}.json"


async def liste_traj(request):
    DOSSIER_TRAJ.mkdir(exist_ok=True)
    return web.json_response(sorted(p.stem for p in DOSSIER_TRAJ.glob("*.json")))


async def lire_traj(request):
    f = nom_fichier(request.match_info["nom"])
    if not f.exists():
        raise web.HTTPNotFound()
    return web.json_response(json.loads(f.read_text(encoding="utf-8")))


async def ecrire_traj(request):
    f = nom_fichier(request.match_info["nom"])
    donnees = await request.json()
    DOSSIER_TRAJ.mkdir(exist_ok=True)
    f.write_text(json.dumps(donnees, indent=1, ensure_ascii=False), encoding="utf-8")
    return web.json_response({"ok": True})


async def suppr_traj(request):
    f = nom_fichier(request.match_info["nom"])
    if f.exists():
        f.unlink()
    return web.json_response({"ok": True})


async def index(request):
    return web.FileResponse(DOSSIER_WEB / "index.html")


async def diffusion_periodique(app):
    async def boucle():
        while True:
            await asyncio.sleep(0.1)
            if clients and (robot.occupe or robot.plan):
                diffuser(robot.etat())
    app["diffusion"] = asyncio.ensure_future(boucle())


async def a_l_arret(app):
    app["diffusion"].cancel()
    await robot.deconnecter()


async def au_demarrage_serie(app):
    port = app["serie"]
    if port:
        try:
            await robot.connecter(port)
        except (ErreurCommande, OSError) as e:
            print(f"Connexion automatique impossible : {e}")


def adresses_locales():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def main():
    global robot
    p = argparse.ArgumentParser(description="Interface web de commande du bras MKX3D")
    p.add_argument("--hote", default="0.0.0.0", help="adresse d'écoute (0.0.0.0 = tout le réseau local)")
    p.add_argument("--port-web", type=int, default=8080)
    p.add_argument("--serie", default=None, help="port série à ouvrir au démarrage, ou 'simulateur'")
    args = p.parse_args()

    robot = Robot(diffuser)
    app = web.Application()
    app["serie"] = args.serie
    app.router.add_get("/", index)
    app.router.add_get("/ws", route_ws)
    app.router.add_get("/api/trajectoires", liste_traj)
    app.router.add_get("/api/trajectoires/{nom}", lire_traj)
    app.router.add_put("/api/trajectoires/{nom}", ecrire_traj)
    app.router.add_delete("/api/trajectoires/{nom}", suppr_traj)
    app.router.add_static("/", DOSSIER_WEB)
    app.on_startup.append(diffusion_periodique)
    app.on_startup.append(au_demarrage_serie)
    app.on_cleanup.append(a_l_arret)

    ip = adresses_locales()
    print(f"Interface MKX3D : http://localhost:{args.port_web}")
    if ip and args.hote == "0.0.0.0":
        print(f"Depuis un autre appareil du réseau : http://{ip}:{args.port_web}")
    web.run_app(app, host=args.hote, port=args.port_web, print=None)


if __name__ == "__main__":
    main()
