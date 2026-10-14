"""Ejecuta la actividad 4 contra GraphQL y MySQL sin dejar cambios en la matriz."""

import json
import os
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4

import pymysql


URL = os.getenv("GRAPHQL_URL", "http://127.0.0.1:8000/graphql")
OUT = Path(__file__).resolve().parent.parent / "evidencias" / "actividad4"
OUT.mkdir(parents=True, exist_ok=True)
CAPTURE_DIR = OUT / "capturas_graphql"
CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
DB = dict(host="127.0.0.1", port=3307, user="actividad4", password="actividad4", database="actividad4_db")
MATRIX = {
    "ADMINISTRADOR": {"company.users.read", "company.users.write", "accounts.read", "accounts.write", "concepts.read", "concepts.write", "transactions.read", "transactions.write", "roles.read", "roles.write"},
    "CONTADOR": {"company.users.read", "accounts.read", "accounts.write", "concepts.read", "concepts.write", "transactions.read", "transactions.write", "roles.read"},
    "CAPTURISTA": {"accounts.read", "concepts.read", "transactions.read", "transactions.write"},
    "CONSULTA": {"company.users.read", "accounts.read", "concepts.read", "transactions.read"},
}
CAPTURE_NAMES = {
    "01_roles", "02_permisos", "03_matriz_inicial", "03_consulta_inicial",
    "03_contador_inicial", "maria_antes", "jose_antes", "08_ana_agrega_permiso",
    "maria_despues", "jose_despues", "10_ana_quita_permiso", "maria_retiro",
    "jose_retiro", "15_pedro_consulta_rechazado", "16_pedro_cambia_rol",
    "17_pedro_capturista_aceptado", "18_contador_despues",
    "18_consulta_despues", "luis_contador", "20_jose_permiso_rechazado",
    "21_ana_permiso_aceptado", "22_ana_restaura_consulta",
}
PAGE = None


def save(name, rule, query=None, result=None, sql=None):
    payload = {"regla": rule}
    if query is not None:
        payload["graphql"] = re.sub(r'password:\s*"[^"]*"', 'password: "[OCULTO]"', query)
        payload["respuesta"] = result
    if sql is not None:
        payload["mysql"] = sql
    (OUT / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(name, "OK")


def gql(name, rule, query, token=None, denied=False):
    if PAGE is None:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = Request(URL, data=json.dumps({"query": query}).encode(), headers=headers)
        with urlopen(req, timeout=30) as response:
            result = json.load(response)
    else:
        PAGE.evaluate('(query) => document.querySelectorAll(".CodeMirror")[0].CodeMirror.setValue(query)', query)
        PAGE.locator("button").nth(8).click()
        PAGE.evaluate('document.querySelectorAll(".CodeMirror")[0].CodeMirror.setOption("lineWrapping", true)')
        browser_headers = {"Authorization": f"Bearer {token}"} if token else {}
        PAGE.evaluate('(headers) => document.querySelectorAll(".CodeMirror")[2].CodeMirror.setValue(JSON.stringify(headers))', browser_headers)
        with PAGE.expect_response(lambda response: response.url.startswith(URL) and response.request.method == "POST", timeout=30000) as response_info:
            PAGE.locator("button").nth(7).click()
        result = response_info.value.json()
        if name in CAPTURE_NAMES:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                shown = PAGE.evaluate('document.querySelectorAll(".CodeMirror")[3].CodeMirror.getValue()')
                try:
                    if json.loads(shown) == result:
                        break
                except json.JSONDecodeError:
                    pass
                PAGE.wait_for_timeout(100)
            else:
                raise AssertionError(f"GraphiQL no mostró la respuesta de {name}")
            PAGE.screenshot(path=str(CAPTURE_DIR / f"{name}.png"))
    assert bool(result.get("errors")) == denied, (name, result)
    save(name, rule, query, result)
    return result.get("data") or {}


def sql(query, args=()):
    with pymysql.connect(**DB, cursorclass=pymysql.cursors.DictCursor) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            return cursor.fetchall()


def quote(value):
    return json.dumps(value, ensure_ascii=False)


def role_codes(role_id):
    result = gql("temporal_lista", "Consulta de permisos activos del rol.", f'query {{ rolePermissions(roleId: "{role_id}") {{ permission {{ code }} }} }}')
    (OUT / "temporal_lista.json").unlink()
    return {entry["permission"]["code"] for entry in result["rolePermissions"]}


def record_role_codes(name, role_id, rule):
    result = gql(name, rule, f'query {{ rolePermissions(roleId: "{role_id}") {{ role {{ code }} permission {{ code }} }} }}')
    return {entry["permission"]["code"] for entry in result["rolePermissions"]}


def account(name, actor, company, denied):
    return gql(name.lower().replace(" ", "_"), f"{name}: {'rechazado sin guardar' if denied else 'aceptado y guardado'} según accounts.write.",
               f'mutation {{ createAccount(actorCompanyUserId: "{actor}", input: {{companyId: "{company}", accountType: CASH, name: {quote(name)}}}) {{ id name }} }}', denied=denied)


def main():
    global PAGE
    if os.getenv("CAPTURAR_GRAPHIQL") == "1":
        from playwright.sync_api import sync_playwright
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
        )
        PAGE = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        PAGE.goto(URL)
        PAGE.locator(".CodeMirror").first.wait_for()
    roles = gql("01_roles", "Existen cuatro roles, sin duplicados.", "query { roles { id code isActive } }")["roles"]
    permissions = gql("02_permisos", "Existen diez permisos, sin duplicados.", "query { permissions { id code isActive } }")["permissions"]
    role_ids = {item["code"]: item["id"] for item in roles}
    permission_ids = {item["code"]: item["id"] for item in permissions}
    assert set(role_ids) == set(MATRIX) and len(roles) == 4
    assert set(permission_ids) == MATRIX["ADMINISTRADOR"] and len(permissions) == 10
    for code, expected in MATRIX.items():
        actual = role_codes(role_ids[code])
        assert actual == expected, (code, actual, expected)
    gql("03_matriz_inicial", "Capturista tiene transactions.write y carece de accounts.write.",
        f'query {{ rolePermissions(roleId: "{role_ids["CAPTURISTA"]}") {{ role {{ code }} permission {{ code }} isActive }} }}')
    record_role_codes("03_consulta_inicial", role_ids["CONSULTA"], "CONSULTA tiene solo permisos de lectura.")
    record_role_codes("03_contador_inicial", role_ids["CONTADOR"], "CONTADOR tiene accounts.write y carece de roles.write.")
    initial_count = sql("SELECT COUNT(*) AS n FROM role_permissions")[0]["n"]

    unique = uuid4().hex[:10]
    company = gql("04_empresa", "Las cinco personas comparten una empresa de prueba.",
                  f'mutation {{ createCompany(input: {{name: "Actividad 4 {unique}"}}) {{ id name }} }}')["createCompany"]["id"]
    password = "Actividad4Demo2026!"
    people = {}
    for name in ("Ana", "Luis", "Maria", "Jose", "Pedro"):
        email = f"{name.lower()}-{unique}@example.com"
        if name == "Ana":
            query = f'mutation {{ createCompanyAdmin(input: {{companyId: "{company}", name: "Ana", email: {quote(email)}, password: {quote(password)}}}) {{ id isAdmin }} }}'
            member = gql("05_ana_administradora", "Ana conserva isAdmin y recibe ADMINISTRADOR.", query)["createCompanyAdmin"]
            assert member["isAdmin"]
        else:
            ana = people["Ana"]
            query = f'mutation {{ createCompanyUser(actorCompanyUserId: "{ana["id"]}", input: {{companyId: "{company}", name: {quote(name)}, email: {quote(email)}, password: {quote(password)}}}) {{ id }} }}'
            member = gql(f"05_{name.lower()}_usuario", "Usuario creado en la misma empresa.", query, ana["token"])["createCompanyUser"]
        login_query = f'mutation {{ login(input: {{email: {quote(email)}, password: {quote(password)}}}) {{ token }} }}'
        headers = {"Content-Type": "application/json"}
        with urlopen(Request(URL, data=json.dumps({"query": login_query}).encode(), headers=headers), timeout=30) as response:
            login = json.load(response)
        assert not login.get("errors"), login
        people[name] = {"id": member["id"], "token": login["data"]["login"]["token"]}
    ana_id = people["Ana"]["id"]
    for name, role in (("Luis", "CONTADOR"), ("Maria", "CAPTURISTA"), ("Jose", "CAPTURISTA")):
        gql(f"06_rol_{name.lower()}", f"{name} tiene un rol activo: {role}.",
            f'mutation {{ assignRole(actorCompanyUserId: "{ana_id}", input: {{companyUserId: "{people[name]["id"]}", roleId: "{role_ids[role]}"}}) {{ id role {{ code }} isActive }} }}')
    account("Maria antes", people["Maria"]["id"], company, True)
    account("Jose antes", people["Jose"]["id"], company, True)
    assert not sql("SELECT id FROM accounts WHERE company_id=%s", (company,))

    grant = f'mutation {{ assignPermissionToRole(actorCompanyUserId: "{ana_id}", input: {{roleId: "{role_ids["CAPTURISTA"]}", permissionId: "{permission_ids["accounts.write"]}"}}) {{ role {{ code }} permission {{ code }} isActive }} }}'
    gql("08_ana_agrega_permiso", "Ana agrega accounts.write una vez al rol CAPTURISTA.", grant)
    assert "accounts.write" in role_codes(role_ids["CAPTURISTA"])
    account("Maria despues", people["Maria"]["id"], company, False)
    account("Jose despues", people["Jose"]["id"], company, False)
    assert len(sql("SELECT id FROM accounts WHERE company_id=%s", (company,))) == 2
    remove = f'mutation {{ removePermissionFromRole(actorCompanyUserId: "{ana_id}", roleId: "{role_ids["CAPTURISTA"]}", permissionId: "{permission_ids["accounts.write"]}") }}'
    gql("10_ana_quita_permiso", "Ana desactiva la pareja, conserva su fila.", remove)
    relation = sql("SELECT id, is_active FROM role_permissions WHERE role_id=%s AND permission_id=%s", (role_ids["CAPTURISTA"], permission_ids["accounts.write"]))
    assert len(relation) == 1 and relation[0]["is_active"] == 0
    save("11_pareja_inactiva_mysql", "La pareja CAPTURISTA/accounts.write permanece en MySQL con is_active=0.", sql={"consulta": "SELECT id, is_active FROM role_permissions WHERE role_id=CAPTURISTA AND permission_id=accounts.write", "filas": relation})
    account("Maria retiro", people["Maria"]["id"], company, True)
    account("Jose retiro", people["Jose"]["id"], company, True)
    assert len(sql("SELECT id FROM accounts WHERE company_id=%s", (company,))) == 2

    cash = account("Caja movimientos", ana_id, company, False)["createAccount"]["id"]
    concept = gql("13_concepto", "Ana crea el concepto de ingresos.",
                  f'mutation {{ createConcept(actorCompanyUserId: "{ana_id}", input: {{companyId: "{company}", conceptType: INCOME, name: "Ingresos actividad 4"}}) {{ id }} }}')["createConcept"]["id"]
    gql("14_asignar_concepto", "El concepto queda disponible para la cuenta.",
        f'mutation {{ assignConceptToAccount(actorCompanyUserId: "{ana_id}", input: {{accountId: "{cash}", conceptId: "{concept}"}}) {{ id }} }}')
    pedro = people["Pedro"]
    transaction = f'mutation {{ createTransaction(actorCompanyUserId: "{pedro["id"]}", input: {{accountId: "{cash}", conceptId: "{concept}", transactionType: INCOME, amount: "125.00"}}) {{ id amount }} }}'
    gql("15_pedro_consulta_rechazado", "CONSULTA carece de transactions.write; no se guarda movimiento.", transaction, pedro["token"], True)
    assert not sql("SELECT id FROM transactions WHERE account_id=%s", (cash,))
    contador_before = record_role_codes("15_contador_antes_cambio", role_ids["CONTADOR"], "Lista de CONTADOR antes de cambiar el rol de Pedro.")
    consulta_before = record_role_codes("15_consulta_antes_cambio", role_ids["CONSULTA"], "Lista de CONSULTA antes de cambiar el rol de Pedro.")
    gql("16_pedro_cambia_rol", "assignRole desactiva CONSULTA y activa CAPTURISTA solo para Pedro.",
        f'mutation {{ assignRole(actorCompanyUserId: "{ana_id}", input: {{companyUserId: "{pedro["id"]}", roleId: "{role_ids["CAPTURISTA"]}"}}) {{ role {{ code }} isActive }} }}')
    gql("17_pedro_capturista_aceptado", "Pedro ahora tiene transactions.write y guarda el movimiento.", transaction, pedro["token"])
    assert len(sql("SELECT id FROM transactions WHERE account_id=%s", (cash,))) == 1
    assignments = sql("SELECT r.code, cur.is_active FROM company_user_roles cur JOIN roles r ON r.id=cur.role_id WHERE cur.company_user_id=%s ORDER BY r.code", (pedro["id"],))
    assert sum(row["is_active"] for row in assignments) == 1
    contador_after = record_role_codes("18_contador_despues", role_ids["CONTADOR"], "CONTADOR conserva la misma lista después del cambio de Pedro.")
    consulta_after = record_role_codes("18_consulta_despues", role_ids["CONSULTA"], "CONSULTA conserva la misma lista después del cambio de Pedro.")
    assert contador_after == contador_before
    assert consulta_after == consulta_before
    save("18_roles_pedro_mysql", "Pedro tiene un solo rol activo; CONTADOR y CONSULTA no cambiaron.", sql={"consulta": "SELECT r.code, cur.is_active FROM company_user_roles cur JOIN roles r ON r.id=cur.role_id WHERE cur.company_user_id=Pedro", "filas": assignments})
    account("Luis contador", people["Luis"]["id"], company, False)

    jose_grant = f'mutation {{ assignPermissionToRole(actorCompanyUserId: "{people["Jose"]["id"]}", input: {{roleId: "{role_ids["CONSULTA"]}", permissionId: "{permission_ids["concepts.write"]}"}}) {{ isActive }} }}'
    gql("20_jose_permiso_rechazado", "José carece de roles.write y no cambia la matriz.", jose_grant, denied=True)
    assert role_codes(role_ids["CONSULTA"]) == consulta_before
    ana_grant = f'mutation {{ assignPermissionToRole(actorCompanyUserId: "{ana_id}", input: {{roleId: "{role_ids["CONSULTA"]}", permissionId: "{permission_ids["concepts.write"]}"}}) {{ isActive }} }}'
    gql("21_ana_permiso_aceptado", "Ana tiene roles.write y puede cambiar CONSULTA.", ana_grant)
    assert "concepts.write" in role_codes(role_ids["CONSULTA"])
    gql("22_ana_restaura_consulta", "Ana retira concepts.write; CONSULTA vuelve a solo lectura.",
        f'mutation {{ removePermissionFromRole(actorCompanyUserId: "{ana_id}", roleId: "{role_ids["CONSULTA"]}", permissionId: "{permission_ids["concepts.write"]}") }}')

    for code, expected in MATRIX.items():
        assert role_codes(role_ids[code]) == expected
    final_count = sql("SELECT COUNT(*) AS n FROM role_permissions")[0]["n"]
    assert initial_count <= final_count <= initial_count + 2
    final_query = "SELECT r.code AS rol, p.code AS permiso, rp.is_active FROM role_permissions rp JOIN roles r ON r.id=rp.role_id JOIN permissions p ON p.id=rp.permission_id ORDER BY r.code, p.code"
    final_rows = sql(final_query)
    assert {(r["rol"], r["permiso"]) for r in final_rows if r["is_active"]} == {(role, permission) for role, codes in MATRIX.items() for permission in codes}
    save("23_matriz_final_mysql", "Los 26 permisos activos coinciden con la tabla; dos parejas históricas quedan inactivas.", sql={"consulta": final_query, "filas": final_rows})
    save("24_identificadores", "Identificadores de la empresa de demostración para repetir las consultas en GraphiQL.", sql={"empresa": company, "personas": {name: data["id"] for name, data in people.items()}, "roles": role_ids, "permisos": permission_ids, "cuenta": cash, "concepto": concept})
    print("ACTIVIDAD 4 COMPLETA. Matriz original restaurada.")
    if PAGE is not None:
        browser.close()
        playwright.stop()


if __name__ == "__main__":
    main()
