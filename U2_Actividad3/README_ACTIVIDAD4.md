# Unidad II · Actividad 4: configuración de permisos por rol

Continuación del Sistema General de Ingresos y de la actividad 3. Se conserva el esquema Python, Strawberry, GraphQL, MySQL y Docker Compose. Los permisos pertenecen a `role_permissions`; cada membresía activa usa un rol de `company_user_roles`.

## Resultado

- Cuatro roles y diez permisos iniciales. La matriz tiene 26 parejas activas.
- Ana agrega `accounts.write` a CAPTURISTA. María y José pueden crear cuentas sin cambiar sus membresías.
- Ana retira el permiso. Ambos vuelven a recibir rechazo y la pareja permanece con `is_active = 0`.
- Pedro pasa de CONSULTA a CAPTURISTA. Su rol anterior queda inactivo, registra un movimiento y no cambian las listas de CONTADOR ni CONSULTA.
- José no puede modificar la lista porque no tiene `roles.write`; Ana sí puede y la restaura.
- Tras reiniciar: 4 roles, 10 permisos, 26 parejas activas y 2 parejas históricas inactivas, sin duplicados.

## Evidencias

Las capturas de [GraphiQL](evidencias/actividad4/capturas_graphql/) muestran consultas ejecutadas contra el servidor local y su respuesta. Cada archivo JSON del mismo nombre conserva la consulta, la respuesta y la regla comprobada. Los identificadores de la ejecución están en [`24_identificadores.json`](evidencias/actividad4/24_identificadores.json). Las contraseñas se ocultan en los JSON y no se publican tokens.

| Captura | Regla demostrada |
| --- | --- |
| [03_matriz_inicial.png](evidencias/actividad4/capturas_graphql/03_matriz_inicial.png) | CAPTURISTA tiene `transactions.write` y carece de `accounts.write`. |
| [maria_antes.png](evidencias/actividad4/capturas_graphql/maria_antes.png) | María no puede crear una cuenta antes del cambio. |
| [jose_antes.png](evidencias/actividad4/capturas_graphql/jose_antes.png) | José tampoco puede crear una cuenta antes del cambio. |
| [08_ana_agrega_permiso.png](evidencias/actividad4/capturas_graphql/08_ana_agrega_permiso.png) | Ana agrega `accounts.write` al rol CAPTURISTA. |
| [maria_despues.png](evidencias/actividad4/capturas_graphql/maria_despues.png) | María crea una cuenta con el permiso nuevo del rol. |
| [jose_despues.png](evidencias/actividad4/capturas_graphql/jose_despues.png) | José crea una cuenta sin editar su membresía. |
| [10_ana_quita_permiso.png](evidencias/actividad4/capturas_graphql/10_ana_quita_permiso.png) | Ana desactiva la pareja del permiso. |
| [maria_retiro.png](evidencias/actividad4/capturas_graphql/maria_retiro.png) | María vuelve a recibir rechazo. |
| [jose_retiro.png](evidencias/actividad4/capturas_graphql/jose_retiro.png) | José vuelve a recibir rechazo. |
| [15_pedro_consulta_rechazado.png](evidencias/actividad4/capturas_graphql/15_pedro_consulta_rechazado.png) | CONSULTA no puede registrar movimientos; MySQL confirma que no se insertó una fila. |
| [16_pedro_cambia_rol.png](evidencias/actividad4/capturas_graphql/16_pedro_cambia_rol.png) | `assignRole` activa CAPTURISTA para Pedro. |
| [17_pedro_capturista_aceptado.png](evidencias/actividad4/capturas_graphql/17_pedro_capturista_aceptado.png) | Pedro registra el movimiento con su nuevo rol. |
| [luis_contador.png](evidencias/actividad4/capturas_graphql/luis_contador.png) | Luis conserva `accounts.write` y crea una cuenta. |
| [20_jose_permiso_rechazado.png](evidencias/actividad4/capturas_graphql/20_jose_permiso_rechazado.png) | José carece de `roles.write`; la lista no cambia. |
| [21_ana_permiso_aceptado.png](evidencias/actividad4/capturas_graphql/21_ana_permiso_aceptado.png) | Ana sí puede modificar la lista de CONSULTA. |
| [22_ana_restaura_consulta.png](evidencias/actividad4/capturas_graphql/22_ana_restaura_consulta.png) | Ana retira `concepts.write`; CONSULTA vuelve a solo lectura. |

La [pareja inactiva](evidencias/actividad4/11_pareja_inactiva_mysql.json), los [roles de Pedro](evidencias/actividad4/18_roles_pedro_mysql.json), el [SELECT final de `role_permissions`](evidencias/actividad4/23_matriz_final_mysql.json) y la [verificación tras reiniciar](evidencias/actividad4/25_reinicio_sin_duplicados.json) incluyen resultados directos de MySQL. El SELECT final muestra las 26 parejas activas de la tabla de la actividad y dos filas inactivas conservadas como historial.

## Reproducir

Requiere Python 3.12, Docker y el puerto 3307 libre. Desde esta carpeta:

```bash
docker compose up -d db
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
export SECRET_KEY='clave-local-para-pruebas'
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```bash
.venv/bin/python documentacion/probar_actividad4.py
.venv/bin/python -m unittest discover -s tests -v
```

Para generar capturas desde GraphiQL se requiere `playwright` instalado en el entorno y Google Chrome disponible; ejecutar `CAPTURAR_GRAPHIQL=1 .venv/bin/python documentacion/probar_actividad4.py`. Tras reiniciar el servidor, ejecutar `.venv/bin/python documentacion/verificar_reinicio_actividad4.py`.

El guion crea una empresa y cinco usuarios nuevos para no depender de datos anteriores. Al terminar, retira los dos permisos agregados y comprueba que la matriz activa coincide con la tabla original. `actorCompanyUserId` sigue siendo el mecanismo didáctico de la actividad 3; no sustituye una autenticación completa del actor en un sistema de producción.
