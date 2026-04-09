"""
Maquina de Turing - Laboratorio
================================
INSTRUCCIONES:
  1. Trabaja directamente sobre el archivo "turing_machine.py".
  2. La clase TuringMachine y su __init__ YA ESTAN DEFINIDOS: cargan el JSON y
     arman la cinta en unario. Tu trabajo es implementar los demas metodos
     donde dice "raise NotImplementedError(...)".
  3. NO cambies los nombres de los metodos ni sus parametros.
  4. NO modifiques main.py.
  5. Lee con atencion los docstrings y los comentarios # antes de cada raise.

NOTA SOBRE LA ESTRUCTURA DE ESTE ARCHIVO
───────────────────────────────────────
- Los docstrings explican la TEORIA y el algoritmo de cada metodo pendiente.
- Los comentarios con # antes de cada raise son la GUIA LINEA A LINEA: traducelos
  a Python, coloca el codigo debajo y elimina ese raise cuando el metodo funcione.

GUIA DE PRUEBAS (como probar cada metodo)
──────────────────────────────────────────
Ejecuta estas pruebas desde la carpeta turing_lab (el unico microcodigo
incluido como referencia es microcodes/suma.json; el resto lo creas tu).

1) Abrir una consola interactiva (recomendado)
       cd turing_lab
       python -i -c "from turing_machine import TuringMachine"

   O en una sola linea por comando:
       cd turing_lab && python -c "from turing_machine import TuringMachine; ..."

2) Objeto base (el __init__ ya funciona)
       tm = TuringMachine("microcodes/suma.json", [3, 2])
       tm.tape     # esperado: ['1','1','1','0','1','1']
       tm.head     # esperado: 0
       tm.state    # esperado: 'q0' (ver initial_state en el JSON)

3) get_state()
       tm.get_state() == tm.state == "q0"
       Tras varios step() hasta llegar a halt, debe coincidir con "halt".

4) get_head_pos()
       tm.get_head_pos() == tm.head
       Debe ser 0 al crear; despues cambia segun las transiciones (R/L/N).

5) is_halted()
       Al inicio: tm.is_halted() → False (mientras state no este en halt_states).
       Cuando tm.state sea "halt" (o el JSON indique otro estado final):
       tm.is_halted() → True.

6) get_tape_window(center, width)   [width impar, ej. 19 en la GUI]
       Con la cinta de [3, 2] y tm.head == 0, prueba centrar en el cabezal:
       tm.get_tape_window(0, 7)
       # Debe tener longitud 7; los indices negativos se rellenan con tm.blank ('_').
       Comparacion manual: mitad = 7//2 = 3 → indices -3..+3 alrededor de 0.

       Prueba borde derecho (simula cinta corta o cabezal al final):
       Si tm.tape == ['1','1','1'] y tm.head == 2,
       tm.get_tape_window(2, 7) deberia mostrar mas '_' a la derecha.

7) get_last_transition()
       Antes del primer paso: tm.get_last_transition() → {}
       Despues de un step() exitoso: dict con claves exactas
       'from_state', 'symbol_read', 'to_state', 'wrote', 'moved'.
       Ejemplo primer paso con suma y [3,2] (lee '1' en q0):
       esperarias moved 'R', wrote '1', to_state 'q0', from_state 'q0'.

8) step()
       tm = TuringMachine("microcodes/suma.json", [3, 2])
       tm.step()  → True
       tm.head    → 1  (primera regla de q0 con '1' mueve R)
       tm.get_last_transition()['moved'] == 'R'

       Si llamas step() cuando ya esta en halt:
       tm.state = 'halt' (o fuerza is_halted True); step() → False

       Si no hay transicion para (estado, simbolo): step() → False sin lanzar error.

9) Prueba de integracion
       python main.py   → carga el JSON, registros, boton paso a paso y tabla.
       Si un metodo falta, veras el error o datos inconsistentes en pantalla.

10) Registro vacio
       tm0 = TuringMachine("microcodes/suma.json", [])
       tm0.tape → ['_']   # un solo blanco

"""

import json
from pathlib import Path


class TuringMachine:
    """
    Simulador de Maquina de Turing determinista con cinta infinita.

    REPRESENTACION DE DATOS EN LA CINTA:
    ─────────────────────────────────────
    Los numeros se codifican en notacion UNARIA:
        n  →  n simbolos '1' consecutivos
        0  →  ninguno (cinta vacia / blanco)

    Separador entre registros: '0'
    Simbolo blanco (celda vacia): '_'

    Ejemplos:
        registros [3, 2]  →  cinta: ['1','1','1','0','1','1']
        registros [0, 4]  →  cinta: ['0','1','1','1','1']
        registros [5]     →  cinta: ['1','1','1','1','1']
        registros []      →  cinta: ['_']

    COMO FUNCIONA LA MAQUINA:
    ──────────────────────────
    En cada paso (step):
      1. Lee el simbolo bajo el cabezal: tape[head]
      2. Busca la regla en transitions[estado_actual][simbolo_leido]
      3. Escribe el nuevo simbolo en tape[head]
      4. Mueve el cabezal: R (derecha), L (izquierda), N (no mover)
      5. Cambia al nuevo estado
      6. Si el nuevo estado es un halt_state → la maquina para
    """

    def __init__(self, config_file: str, registers: list):
        """
        Carga el microcodigo (JSON) y construye la cinta en notacion unario.

        YA ESTA IMPLEMENTADO — no es parte del ejercicio. Tras ejecutarse tendras:

            self.config       dict completo del JSON (la GUI muestra transiciones)
            self.blank        simbolo de celda vacia (por defecto '_')
            self.state        estado actual, empieza en initial_state del JSON
            self.halt_states  conjunto de estados de parada
            self.transitions  reglas: transitions[estado][simbolo] -> accion
            self._last_trans  {} al inicio; step() lo rellena tras cada paso
            self.tape         lista de caracteres (la cinta)
            self.head         indice del cabezal (comienza en 0)

        PARAMETROS:
            config_file : ruta al JSON (ej: "microcodes/suma.json")
            registers   : enteros no negativos (ej: [3, 2])
        """
        # Permite ejecutar desde cualquier cwd: si la ruta es relativa y no existe,
        # la resolvemos relativa a esta carpeta (Turing-Machine-UMA/).
        cfg_path = Path(config_file)
        if not cfg_path.is_absolute() and not cfg_path.is_file():
            cfg_path = (Path(__file__).resolve().parent / cfg_path)

        with open(cfg_path, 'r') as f:
            self.config = json.load(f)

        self.blank = self.config.get('blank_symbol', '_')
        self.state = self.config['initial_state']
        self.halt_states = set(self.config['halt_states'])
        self.transitions = self.config['transitions']
        self._last_trans = {}

        parts = []
        for i, r in enumerate(registers):
            parts.extend(['1'] * r)
            if i < len(registers) - 1:
                parts.append('0')

        self.tape = parts if parts else [self.blank]
        self.head = 0

    # ══════════════════════════════════════════════════════════════════════
    # A PARTIR DE AQUI: tu trabajo es implementar los metodos (quita los raise).
    # ══════════════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════════════
    # METODOS DE CONSULTA — solo LEEN el estado, no lo modifican
    # ══════════════════════════════════════════════════════════════════════

    def get_state(self) -> str:
        """
        Retorna el estado actual de la maquina.

        PSEUDOCODIGO:
            retornar self.state

        EJEMPLO DE RETORNO: "q0", "q1", "halt"
        """
        # === GUIA LINEA A LINEA (get_state) ===
        # L1  retornar self.state  (una sola linea de codigo)
        return self.state

    def get_head_pos(self) -> int:
        """
        Retorna la posicion actual del cabezal.

        PSEUDOCODIGO:
            retornar self.head

        NOTA: El cabezal comienza en 0 y puede crecer hacia la derecha.
        """
        # === GUIA LINEA A LINEA (get_head_pos) ===
        # L1  retornar self.head  (una sola linea de codigo)
        return self.head

    def is_halted(self) -> bool:
        """
        Retorna True si la maquina ha llegado a un estado de parada.

        PSEUDOCODIGO:
            retornar (self.state esta dentro de self.halt_states)

        PISTA: usa el operador 'in':
               return self.state in self.halt_states

        EJEMPLO: si halt_states = {'halt'} y state = 'halt' → True
                 si halt_states = {'halt'} y state = 'q0'   → False
        """
        # === GUIA LINEA A LINEA (is_halted) ===
        # L1  retornar True si self.state pertenece a self.halt_states, False si no
        #     Pseudocodigo: return self.state in self.halt_states
        return self.state in self.halt_states

    def get_tape_window(self, center: int, width: int) -> list:
        """
        Retorna una ventana de la cinta de 'width' simbolos centrada en 'center'.

        Si la posicion cae fuera de la cinta (indice < 0 o >= len(tape)),
        rellena con el simbolo blanco (self.blank).

        PARAMETROS:
            center : indice del centro de la ventana (= posicion del cabezal)
            width  : numero de celdas a retornar (siempre impar, ej: 19)

        RETORNA:
            Lista de 'width' cadenas de un caracter.

        ALGORITMO:
            resultado = []
            mitad = width // 2              # mitad de la ventana (cuantas celdas a cada lado)

            para i desde (center - mitad) hasta (center + mitad) inclusive:
                si i < 0 o i >= len(self.tape):
                    agregar self.blank al resultado    # fuera de rango → blanco
                si no:
                    agregar self.tape[i] al resultado  # dentro de rango → simbolo real

            retornar resultado

        PSEUDOCODIGO Python:
            resultado = []
            mitad = width // 2
            for i in range(center - mitad, center + mitad + 1):
                if i < 0 or i >= len(self.tape):
                    resultado.append(self.blank)
                else:
                    resultado.append(self.tape[i])
            return resultado

        EJEMPLO:
            tape = ['1','1','1','0','1','1'], blank = '_', center = 2, width = 7
            mitad = 3, rango: -1, 0, 1, 2, 3, 4, 5
              i=-1 → fuera → '_'
              i=0  → tape[0] = '1'
              i=1  → tape[1] = '1'
              i=2  → tape[2] = '1'
              i=3  → tape[3] = '0'
              i=4  → tape[4] = '1'
              i=5  → tape[5] = '1'
            Resultado: ['_','1','1','1','0','1','1']

        CASO BORDE DERECHO (head cerca del fin de la cinta):
            tape = ['1','1','1'], blank = '_', center = 2, width = 7
            mitad = 3, rango: -1, 0, 1, 2, 3, 4, 5
              i=3,4,5 → >= len(tape) = 3 → '_'
            Resultado: ['_','1','1','1','_','_','_']
        """
        # === GUIA LINEA A LINEA (get_tape_window) ===
        # L1  resultado ← lista vacia
        # L2  mitad ← width // 2   (celdas a izquierda y derecha del centro)
        # L3  para i en range(center - mitad, center + mitad + 1):  # inclusivo en ambos extremos
        # L4      si i < 0 o i >= len(self.tape):
        # L5          append self.blank a resultado   # "cinta infinita" simulada con blancos
        # L6      si no:
        # L7          append self.tape[i] a resultado
        # L8  retornar resultado
        result = []
        half = width // 2
        for i in range(center - half, center + half + 1):
            if i < 0 or i >= len(self.tape):
                result.append(self.blank)
            else:
                result.append(self.tape[i])
        return result

    def get_last_transition(self) -> dict:
        """
        Retorna la informacion de la ultima transicion ejecutada.

        Si no se ha ejecutado ningun paso, retorna un diccionario vacio {}.

        PSEUDOCODIGO:
            retornar self._last_trans

        FORMATO DEL DICCIONARIO (cuando hay una transicion):
            {
                "from_state":  "q0",   # estado ANTES del paso
                "symbol_read": "1",    # simbolo que se LEYO
                "to_state":    "q1",   # estado DESPUES del paso
                "wrote":       "1",    # simbolo que se ESCRIBIO
                "moved":       "R"     # direccion: "R", "L" o "N"
            }

        NOTA: Este diccionario se llena en el metodo step().
              Aqui solo hay que retornarlo.
        """
        # === GUIA LINEA A LINEA (get_last_transition) ===
        # L1  retornar self._last_trans  (sin modificarlo; puede ser {} al inicio)
        return self._last_trans

    # ══════════════════════════════════════════════════════════════════════
    # METODO DE EJECUCION — el corazon de la maquina
    # ══════════════════════════════════════════════════════════════════════

    def step(self) -> bool:
        """
        Ejecuta UN paso de la maquina de Turing.

        RETORNA:
            True  → se ejecuto un paso correctamente
            False → la maquina ya estaba detenida O no existe transicion
                    para el estado y simbolo actuales

        ═══════════════════════════════════════════════════════════
        PASO A: Verificar si la maquina ya esta detenida
        ═══════════════════════════════════════════════════════════
        Si is_halted() es True, retornar False inmediatamente.
        No hay nada que hacer.

        Pseudocodigo:
            si self.is_halted():
                retornar False

        ═══════════════════════════════════════════════════════════
        PASO B: Leer el simbolo actual bajo el cabezal
        ═══════════════════════════════════════════════════════════
        El simbolo esta en self.tape[self.head].

        Pseudocodigo:
            simbolo_actual = self.tape[self.head]

        ═══════════════════════════════════════════════════════════
        PASO C: Buscar la transicion en el diccionario
        ═══════════════════════════════════════════════════════════
        La funcion de transicion esta en self.transitions.
        Es un diccionario anidado: transitions[estado][simbolo] = accion

        Pseudocodigo:
            transiciones_del_estado = self.transitions.get(self.state, {})
            accion = transiciones_del_estado.get(simbolo_actual)

        Si accion es None (no existe transicion para este par estado/simbolo):
            retornar False   ← la maquina se detiene silenciosamente

        ═══════════════════════════════════════════════════════════
        PASO D: Guardar el estado anterior (lo necesitamos para el log)
        ═══════════════════════════════════════════════════════════
        Pseudocodigo:
            estado_anterior = self.state

        ═══════════════════════════════════════════════════════════
        PASO E: Escribir el nuevo simbolo en la cinta
        ═══════════════════════════════════════════════════════════
        La accion tiene el campo 'write' con el simbolo a escribir.

        Pseudocodigo:
            self.tape[self.head] = accion['write']

        ═══════════════════════════════════════════════════════════
        PASO F: Guardar la informacion de esta transicion
        ═══════════════════════════════════════════════════════════
        Llena self._last_trans con un diccionario que tenga:
            - 'from_state'  : estado_anterior
            - 'symbol_read' : simbolo_actual
            - 'to_state'    : accion['next_state']
            - 'wrote'       : accion['write']
            - 'moved'       : accion['move']

        Pseudocodigo:
            self._last_trans = {
                'from_state':  estado_anterior,
                'symbol_read': simbolo_actual,
                'to_state':    accion['next_state'],
                'wrote':       accion['write'],
                'moved':       accion['move'],
            }

        ═══════════════════════════════════════════════════════════
        PASO G: Mover el cabezal segun la direccion
        ═══════════════════════════════════════════════════════════
        La direccion esta en accion['move']. Puede ser:
            'R' → mover a la derecha: self.head += 1
                  Si el cabezal sale por la derecha de la cinta,
                  EXPANDIR la cinta agregando un blanco al final:
                      if self.head >= len(self.tape):
                          self.tape.append(self.blank)

            'L' → mover a la izquierda: self.head -= 1
                  IMPORTANTE: no puede ir a la izquierda del inicio.
                  Si self.head == 0, NO mover (clamp):
                      if self.head > 0:
                          self.head -= 1

            'N' → no mover (el cabezal permanece en su posicion actual)

        Pseudocodigo:
            direccion = accion['move']
            si direccion == 'R':
                self.head += 1
                si self.head >= len(self.tape):
                    self.tape.append(self.blank)
            sino si direccion == 'L':
                si self.head > 0:
                    self.head -= 1
            # si 'N': no hacer nada

        ═══════════════════════════════════════════════════════════
        PASO H: Cambiar al nuevo estado
        ═══════════════════════════════════════════════════════════
        Pseudocodigo:
            self.state = accion['next_state']

        ═══════════════════════════════════════════════════════════
        PASO I: Retornar True (el paso se ejecuto correctamente)
        ═══════════════════════════════════════════════════════════
        Pseudocodigo:
            retornar True
        """
        # === GUIA LINEA A LINEA (step) — respeta este ORDEN para coincidir con la GUI ===
        # L1  si self.is_halted(): retornar False   # ya en parada → no avanzar
        # L2  simbolo ← self.tape[self.head]        # leer lo que hay bajo el cabezal
        # L3  Buscar accion en self.transitions SIN romper si falta una clave:
        #     Pseudocodigo: accion = self.transitions.get(self.state, {}).get(simbolo)
        # L4  si accion es None: retornar False     # sin regla definida → detenerse (sin excepcion)
        # L5  estado_previo ← self.state            # guardar ANTES de mutar el estado
        # L6  self.tape[self.head] ← accion['write']   # escribir en la celda actual
        # L7  self._last_trans ← diccionario con claves exactas:
        #        'from_state'  → estado_previo
        #        'symbol_read' → simbolo
        #        'to_state'    → accion['next_state']
        #        'wrote'       → accion['write']
        #        'moved'       → accion['move']
        # L8  dir ← accion['move']   # vale 'R', 'L' o 'N'
        # L9  si dir == 'R': incrementar head en 1; si head >= len(tape), append self.blank
        # L10 si dir == 'L': si head > 0, decrementar head en 1  (no bajar de indice 0)
        # L11 si dir == 'N': no cambiar head
        # L12 self.state ← accion['next_state']   # actualizar estado AL FINAL del paso
        # L13 retornar True
        if self.is_halted():
            return False

        symbol = self.tape[self.head]
        action = self.transitions.get(self.state, {}).get(symbol)
        if action is None:
            return False

        prev_state = self.state

        self.tape[self.head] = action["write"]

        self._last_trans = {
            "from_state": prev_state,
            "symbol_read": symbol,
            "to_state": action["next_state"],
            "wrote": action["write"],
            "moved": action["move"],
        }

        move = action["move"]
        if move == "R":
            self.head += 1
            if self.head >= len(self.tape):
                self.tape.append(self.blank)
        elif move == "L":
            if self.head > 0:
                self.head -= 1
        # "N" -> no mover

        self.state = action["next_state"]
        return True
