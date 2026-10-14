"""Comprueba los catálogos y la matriz después de reiniciar el servidor."""

import json
from pathlib import Path
from urllib.request import Request, urlopen

import pymysql


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "evidencias" / "actividad4" / "25_reinicio_sin_duplicados.json"
QUERY = "SELECT r.code AS rol, p.code AS permiso, rp.is_active FROM role_permissions rp JOIN roles r ON r.id=rp.role_id JOIN permissions p ON p.id=rp.permission_id ORDER BY r.code, p.code"

with pymysql.connect(host="127.0.0.1", port=3307, user="actividad4", password="actividad4", database="actividad4_db", cursorclass=pymysql.cursors.DictCursor) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM roles")
        roles = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM permissions")
        permissions = cur.fetchone()["n"]
        cur.execute(QUERY)
        rows = cur.fetchall()

assert roles == 4 and permissions == 10
assert sum(row["is_active"] for row in rows) == 26
assert len(rows) == 28
assert next(row for row in rows if row["rol"] == "CAPTURISTA" and row["permiso"] == "accounts.write")["is_active"] == 0
assert next(row for row in rows if row["rol"] == "CONSULTA" and row["permiso"] == "concepts.write")["is_active"] == 0

req = Request("http://127.0.0.1:8000/graphql", data=json.dumps({"query": "query { roles { code } permissions { code } }"}).encode(), headers={"Content-Type": "application/json"})
with urlopen(req, timeout=30) as response:
    result = json.load(response)
assert not result.get("errors"), result
assert len(result["data"]["roles"]) == 4 and len(result["data"]["permissions"]) == 10

OUT.write_text(json.dumps({"regla": "Tras reiniciar: 4 roles, 10 permisos, 26 relaciones activas y 2 relaciones históricas inactivas; no hay duplicados.", "consulta_sql": QUERY, "conteos": {"roles": roles, "permissions": permissions, "role_permissions": len(rows), "activas": 26, "inactivas": 2}, "graphql": result, "filas": rows}, ensure_ascii=False, indent=2) + "\n")
print("Reinicio verificado: 4 roles, 10 permisos, 26 parejas activas y 2 inactivas.")
