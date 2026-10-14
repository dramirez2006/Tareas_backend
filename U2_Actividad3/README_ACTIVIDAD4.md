# Actividad 4 - Permisos para los roles

Seguimos con el Sistema General de Ingresos de la actividad 3. Para esta prueba creamos una empresa con Ana (administradora), Luis (contador), María y José (capturistas) y Pedro (consulta). No cambiamos los permisos de cada usuario por separado: cambiamos la lista del rol y comprobamos el resultado en GraphiQL y MySQL.

## Evidencias

Cada enlace abre una captura de `/graphql`. A su lado anotamos qué comprobamos.

### 1. Permisos al iniciar

| Captura | Qué muestra |
| --- | --- |
| [Roles](evidencias/actividad4/capturas_graphql/01_roles.png) | Están ADMINISTRADOR, CONTADOR, CAPTURISTA y CONSULTA. |
| [Permisos](evidencias/actividad4/capturas_graphql/02_permisos.png) | El catálogo tiene los diez permisos de la actividad. |
| [Capturista](evidencias/actividad4/capturas_graphql/03_matriz_inicial.png) | Puede registrar movimientos, pero todavía no puede crear cuentas. |
| [Contador](evidencias/actividad4/capturas_graphql/03_contador_inicial.png) | Tiene `accounts.write` y no tiene `roles.write`. |
| [Consulta](evidencias/actividad4/capturas_graphql/03_consulta_inicial.png) | Tiene permisos de lectura y ningún permiso `.write`. |

### 2. Un cambio en CAPTURISTA afecta a dos personas

| Captura | Qué muestra |
| --- | --- |
| [María antes](evidencias/actividad4/capturas_graphql/maria_antes.png) | `createAccount` se rechaza porque falta `accounts.write`. |
| [José antes](evidencias/actividad4/capturas_graphql/jose_antes.png) | A José le ocurre lo mismo. |
| [Ana agrega el permiso](evidencias/actividad4/capturas_graphql/08_ana_agrega_permiso.png) | Agrega `accounts.write` al rol CAPTURISTA una sola vez. |
| [María después](evidencias/actividad4/capturas_graphql/maria_despues.png) | Ahora crea una cuenta. |
| [José después](evidencias/actividad4/capturas_graphql/jose_despues.png) | También crea una cuenta sin cambiar su rol. |
| [Ana retira el permiso](evidencias/actividad4/capturas_graphql/10_ana_quita_permiso.png) | Desactiva `accounts.write` para CAPTURISTA. |
| [María tras retirarlo](evidencias/actividad4/capturas_graphql/maria_retiro.png) | Su siguiente intento vuelve a rechazarse. |
| [José tras retirarlo](evidencias/actividad4/capturas_graphql/jose_retiro.png) | Su siguiente intento también se rechaza. |

La [captura de MySQL](evidencias/actividad4/08_permiso_inactivo_mysql.png) muestra que la fila CAPTURISTA/`accounts.write` sigue en `role_permissions` con `is_active = 0`. Los intentos rechazados no agregaron cuentas.

### 3. Pedro cambia de puesto

| Captura | Qué muestra |
| --- | --- |
| [Pedro como consulta](evidencias/actividad4/capturas_graphql/15_pedro_consulta_rechazado.png) | No puede registrar un movimiento. Tampoco se guarda una fila nueva. |
| [Cambio de rol](evidencias/actividad4/capturas_graphql/16_pedro_cambia_rol.png) | Ana le asigna CAPTURISTA. |
| [Pedro como capturista](evidencias/actividad4/capturas_graphql/17_pedro_capturista_aceptado.png) | Registra el movimiento con el permiso de su nuevo rol. |
| [Contador después](evidencias/actividad4/capturas_graphql/18_contador_despues.png) | Su lista sigue igual que al inicio. |
| [Consulta después](evidencias/actividad4/capturas_graphql/18_consulta_despues.png) | Su lista también sigue igual. |
| [Luis crea una cuenta](evidencias/actividad4/capturas_graphql/luis_contador.png) | Confirma que el contador conserva `accounts.write`. |

La [consulta a MySQL](evidencias/actividad4/verificaciones_mysql.txt) muestra un solo rol activo para Pedro. Su rol anterior quedó inactivo.

### 4. Quién puede modificar los permisos

| Captura | Qué muestra |
| --- | --- |
| [Intento de José](evidencias/actividad4/capturas_graphql/20_jose_permiso_rechazado.png) | No puede dar `concepts.write` a CONSULTA porque le falta `roles.write`. |
| [Cambio de Ana](evidencias/actividad4/capturas_graphql/21_ana_permiso_aceptado.png) | Ana sí puede agregarlo. |
| [Ana lo retira](evidencias/actividad4/capturas_graphql/22_ana_restaura_consulta.png) | CONSULTA vuelve a quedar sin permisos de escritura. |

La [consulta a MySQL](evidencias/actividad4/verificaciones_mysql.txt) confirma que el intento rechazado de José no activó `concepts.write` para CONSULTA.

## Resultado final en MySQL

Ejecutamos la consulta solicitada:

```sql
SELECT r.code AS rol, p.code AS permiso, rp.is_active
FROM role_permissions rp
JOIN roles r ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
ORDER BY r.code, p.code;
```

La [salida del SELECT en MySQL](evidencias/actividad4/select_final_mysql.txt) deja 26 relaciones activas, iguales a la tabla de la actividad. Las dos relaciones que agregamos y retiramos siguen guardadas como inactivas. Después de reiniciar, [comprobamos](evidencias/actividad4/verificaciones_mysql.txt) que siguen existiendo cuatro roles y diez permisos, sin duplicados.
