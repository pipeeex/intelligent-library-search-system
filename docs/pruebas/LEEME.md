# Gestión de pruebas con Qase

| Archivo | Dónde está | Para qué |
|---|---|---|
| `Plan_de_pruebas.md` | `docs/` | El plan completo: alcance, estrategia, criterios, trazabilidad |
| `casos_prueba_qase.csv` | `docs/pruebas/` | Los 39 casos, listos para importar en Qase |
| `casos_prueba_qase_variante.csv` | `docs/pruebas/` | El mismo archivo con un encabezado alterno, por si el primero falla |
| `generar_casos_qase.py` | `docs/pruebas/` | Regenera el CSV; aquí se editan o añaden casos |
| `publicar_en_qase.py` | raíz del proyecto | Sube a Qase el resultado de la suite automatizada |

Los comandos de este documento se ejecutan desde la raíz del proyecto, salvo
`generar_casos_qase.py`, que se ejecuta desde `docs/pruebas/`.

---

## Puesta en marcha, una sola vez

**1. Crear la cuenta.** En qase.io, con el plan Free. Admite cuatro usuarios:
los tres del equipo y uno libre para el profesor.

**2. Crear el proyecto.** Qase pide un código corto (por ejemplo `SDCIB`).
Anótalo: lo necesitan los dos scripts.

**3. Importar los casos.** En el proyecto, `Test cases` → `Import` → CSV, y
subir `casos_prueba_qase.csv`.

> Si la importación falla, prueben con `casos_prueba_qase_variante.csv`. La única
> diferencia es que una columna se llama `steps_results` en vez de `steps_result`.
> La documentación de Qase se contradice en ese punto y no hay forma de saber
> cuál acepta sin intentarlo. Si fallan las dos, exporten un caso de ejemplo
> desde Qase en CSV, comparen la fila de encabezados con la del archivo y
> ajusten `ENCABEZADOS` en `generar_casos_qase.py`.

**4. Sacar el token de la API.** En Qase, menú de la cuenta → `API Tokens` →
crear uno. Se muestra una sola vez.

**5. Guardar las credenciales.** En Windows, en la misma terminal donde van a
correr el script:

```cmd
set QASE_TOKEN=el-token-que-copiaron
set QASE_PROJECT=SDCIB
```

Para que no haya que repetirlo, pueden añadirlas al `.env` del proyecto, que ya
está fuera del control de versiones. **El token no se sube al repositorio.**

---

## Cada vez que ejecuten las pruebas

```bash
# 1. Con los tres nodos levantados
python herramientas/pruebas_transaccionales.py --nodo 1

# 2. Ver qué se enviaría, sin enviar nada
python publicar_en_qase.py --simular

# 3. Publicar
python publicar_en_qase.py
```

El script toma el informe más reciente de `docs/evidencias/`, crea la ejecución
en Qase con los ocho casos y sus comprobaciones como pasos, y la cierra. Al
final imprime el enlace.

### Enlazar los resultados con los casos importados

La primera vez no hace falta hacer nada: Qase identifica cada caso por su
título. Para que los resultados caigan sobre los casos que ya importaron, en vez
de crear duplicados, creen un archivo `mapeo_casos.json` en la raíz del
proyecto con los identificadores que Qase les asignó:

```json
{
  "PT-01": 7,
  "PT-02": 8,
  "PT-03": 9,
  "PT-04": 10,
  "PT-05": 11,
  "PT-06": 12,
  "PT-07": 13,
  "PT-08": 14
}
```

Los números salen de la columna `ID` del listado de casos en Qase.

---

## Modificar el catálogo

No editen el CSV a mano. Editen `generar_casos_qase.py`, donde cada caso es una
llamada a `caso(...)` con sus pasos y resultados esperados, y vuelvan a generar:

```bash
python generar_casos_qase.py
```

El generador avisa si un caso tiene distinto número de pasos que de resultados
esperados, que es el error más fácil de cometer.

Valores admitidos por Qase, por si añaden casos:

- `prioridad`: `undefined`, `high`, `medium`, `low`
- `severidad`: `undefined`, `blocker`, `critical`, `major`, `normal`, `minor`, `trivial`
- `tipo`: `functional`, `smoke`, `regression`, `security`, `usability`,
  `performance`, `acceptance`, `compatibility`, `integration`, `exploratory`, `other`
- `automatizacion`: `is-not-automated`, `to-be-automated`, `automated`
- `capa`: `unknown`, `e2e`, `api`, `unit`
