# Laboratorio: El Automata Universal
### Programacion — Maquinas de Turing

---

## 1. Introduccion

Una **Maquina de Turing** es un modelo matematico de computacion compuesto por:

- Una **cinta infinita** dividida en celdas, cada una con un simbolo.
- Un **cabezal** que puede leer y escribir sobre la celda actual, y moverse izquierda o derecha.
- Un **estado interno** que determina que accion tomar.
- Una **funcion de transicion** que, dado el estado actual y el simbolo leido, decide: que escribir, hacia donde moverse y a que estado ir.

En este laboratorio vas a implementar el motor de una Maquina de Turing y luego escribiras programas (llamados **microcodigos**) en formato JSON para la **suma** y las **restas** (izquierda-derecha y derecha-izquierda) en unario.

---

## 2. Representacion de datos

Los numeros se codifican en **notacion unaria**:

| Numero | Cinta |
|--------|-------|
| 0      | _(vacio) |
| 1      | `1` |
| 2      | `1 1` |
| 3      | `1 1 1` |
| n      | n simbolos `1` |

Cuando hay dos registros (R0 y R1), se separan con un `0`:

```
R0 = 3, R1 = 2  →  cinta: 1 1 1 0 1 1
```

El simbolo **blanco** `_` representa una celda vacia (la cinta es infinita de blancos hacia ambos lados).

---

## 3. Tu tarea

Debes implementar la clase `TuringMachine` en el archivo **`turing_machine.py`**.

> **Regla de oro:** Solo debes modificar `turing_machine.py`.  
> No toques `main.py`.

---

## 4. API que debes implementar

### Constructor

```python
TuringMachine(config_file: str, registers: list)
```

- `config_file`: ruta al archivo JSON con el microcodigo (p. ej. `"microcodes/suma.json"`)
- `registers`: lista de enteros, p. ej. `[3, 2]`

Debe cargar el JSON, construir la cinta en notacion unaria e inicializar el cabezal en la posicion 0.

### Metodos de consulta

```python
get_state() -> str          # estado actual: "q0", "halt", etc.
get_head_pos() -> int       # indice del cabezal en la cinta
is_halted() -> bool         # True si el estado esta en halt_states
get_last_transition() -> dict  # info del ultimo paso ejecutado (ver abajo)
get_tape_window(center, width) -> list  # ventana de la cinta (ver abajo)
```

#### `get_last_transition()` — formato del diccionario

```python
{
    "from_state":  "q0",   # estado antes del paso
    "symbol_read": "1",    # simbolo que se leyo
    "to_state":    "q1",   # estado despues del paso
    "wrote":       "1",    # simbolo que se escribio
    "moved":       "R"     # direccion: "R", "L" o "N"
}
```

Retorna `{}` si aun no se ha ejecutado ningun paso.

#### `get_tape_window(center, width)` — ventana de la cinta

Retorna una lista de `width` simbolos centrada en `center`.  
Si el indice cae fuera de la cinta, rellena con el simbolo blanco `_`.

```
Cinta: [1, 1, 1, 0, 1, 1],  head = 2
get_tape_window(2, 7)  →  ['_', '_', '1', '1', '1', '0', '1']
```

### Metodo de ejecucion

```python
step() -> bool
```

Ejecuta **un** paso de la maquina:

1. Si ya esta detenida (`is_halted()`), retorna `False`.
2. Lee el simbolo actual.
3. Busca la transicion `transitions[estado_actual][simbolo_leido]`.
4. Si no existe, retorna `False` (sin lanzar excepcion).
5. Si existe: escribe, mueve el cabezal, cambia de estado, guarda la transicion.
6. Retorna `True`.

> La cinta crece automaticamente hacia la derecha si el cabezal sale por ese lado.

---

## 5. Formato del microcodigo JSON

```json
{
    "initial_state": "q0",
    "blank_symbol":  "_",
    "halt_states":   ["halt"],
    "transitions": {
        "q0": {
            "1": { "next_state": "q0", "write": "1", "move": "R" },
            "0": { "next_state": "q1", "write": "1", "move": "R" },
            "_": { "next_state": "halt", "write": "_", "move": "N" }
        },
        "q1": {
            "1": { "next_state": "q1", "write": "1", "move": "R" },
            "_": { "next_state": "q2", "write": "_", "move": "L" }
        },
        "q2": {
            "1": { "next_state": "halt", "write": "_", "move": "N" }
        }
    }
}
```

El archivo **`microcodes/suma.json`** es la **unica referencia** que te entrega el laboratorio: suma en unario (R0 + R1). Usalo para probar tu `TuringMachine` antes de escribir tus propios microcodigos.

---

## 6. Como conectar tu codigo con la interfaz

1. Instala pygame si aun no lo tienes:
   ```
   pip install pygame
   ```

2. Implementa los metodos en `turing_machine.py`.

3. Ejecuta la interfaz:
   ```
   python main.py
   ```

4. En la interfaz:
   - Escribe la ruta del archivo JSON en el campo **"Archivo JSON"**.
   - Escribe los registros en el campo **"Registros"** (separados por espacio).
   - Presiona **Enter** o el boton **Cargar**.
   - Usa **F** para ejecutar paso a paso, **Espacio** para correr automaticamente.

5. Si tu implementacion tiene errores, la interfaz mostrara el mensaje de error en rojo, sin cerrarse.

---

## 7. Microcodigos a entregar

### 7.1 Archivo de referencia (solo lectura; ya viene en `microcodes/`)

| Archivo       | Descripcion |
|---------------|-------------|
| `suma.json`   | Suma en unario: R0 + R1 (ejemplo para probar tu motor) |

### 7.2 Archivos que debes crear

Cuando `suma.json` funcione bien con tu implementacion, debes escribir **tu** version de los siguientes JSON en la carpeta `microcodes/`:

| Archivo         | Descripcion |
|-----------------|-------------|
| `resta_lr.json` | Resta en unario: borra **R1** unos de **R0** recorriendo la primera cifra de **izquierda a derecha** hasta que R1 llegue a 0 |
| `resta_rl.json` | Igual que la anterior, pero borrando de **derecha a izquierda** |

---

## 8. Controles de la interfaz

| Tecla      | Accion |
|------------|--------|
| F          | Ejecutar un paso |
| Espacio    | Ejecutar / Pausar automatico |
| R          | Reiniciar la maquina |
| Flecha Up  | Aumentar velocidad |
| Flecha Down| Disminuir velocidad |
| Tab        | Cambiar campo de texto activo |
| Enter      | Cargar archivo JSON |

---

## 9. Entregables

- [ ] `turing_machine.py` — clase completamente implementada, sin `NotImplementedError`
- [ ] `microcodes/resta_lr.json`
- [ ] `microcodes/resta_rl.json`

Los microcodigos que creaste deben correr en la interfaz y producir el resultado esperado segun las descripciones de la seccion 7.
