"""
Maquina de Turing - Interfaz Visual
====================================
Este archivo es provisto por el profesor. NO MODIFICAR.

Controles:
  F           - Ejecutar un paso
  Espacio     - Ejecutar / Pausar automatico
  R           - Reiniciar la maquina
  Flecha Up   - Aumentar velocidad
  Flecha Down - Disminuir velocidad
  Tab         - Cambiar campo activo
  Enter       - Cargar archivo JSON
  Clic ◀ ▶   - Desplazar la vista de la cinta (pan horizontal; no mueve el cabezal)
"""

import pygame
import sys
import json
import math
import time

# ---------------------------------------------------------------------------
# Importar la clase del alumno de forma segura
# ---------------------------------------------------------------------------
TM_CLASS_AVAILABLE = False
TM_IMPORT_ERROR = ""
TuringMachine = None

try:
    from turing_machine import TuringMachine
    TM_CLASS_AVAILABLE = True
except NotImplementedError:
    TM_IMPORT_ERROR = "TuringMachine lanza NotImplementedError al importar"
except Exception as e:
    TM_IMPORT_ERROR = f"{type(e).__name__}: {e}"

# ---------------------------------------------------------------------------
# Dimensiones
# ---------------------------------------------------------------------------
WIN_W, WIN_H = 1280, 800

# Zonas Y
Y_HEADER   = 0
H_HEADER   = 52
Y_INPUT    = H_HEADER
H_INPUT    = 84
Y_STATUS   = Y_INPUT  + H_INPUT    # 136
H_STATUS   = 52
Y_TAPE     = Y_STATUS + H_STATUS   # 188
H_TAPE     = 244
Y_CONTROLS = Y_TAPE   + H_TAPE     # 432
H_CONTROLS = 64
Y_TTABLE   = Y_CONTROLS + H_CONTROLS  # 496
H_TTABLE   = WIN_H - Y_TTABLE         # 304

CELL_W  = 56
CELL_H  = 56
GAP     = 4
NUM_CELLS = 19  # impar

# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------
# Base
C_BG         = ( 13,  17,  23)   # #0D1117
C_SURFACE    = ( 22,  27,  34)   # #161B22
C_SURFACE2   = ( 28,  33,  40)   # #1C2128
C_BORDER     = ( 48,  54,  61)   # #30363D
C_BORDER_LT  = ( 68,  76,  86)   # lighter border

# Texto
C_TEXT       = (230, 237, 243)   # almost white
C_TEXT_DIM   = (110, 118, 129)
C_TEXT_MUTE  = ( 60,  67,  75)

# Accents
C_BLUE       = ( 88, 166, 255)   # #58A6FF
C_TEAL       = ( 56, 211, 159)   # #38D39F
C_GREEN      = ( 63, 185, 80 )   # #3FB950
C_YELLOW     = (210, 153,  34)   # #D29922
C_RED        = (248,  81,  73)   # #F85149
C_ORANGE     = (219, 109,  40)   # #DB6D28
C_PURPLE     = (188, 140, 255)   # #BC8CFF
C_PINK       = (255, 131, 150)   # #FF8396

# Celdas de la cinta
C_CELL_BG    = ( 22,  27,  34)
C_CELL_ADJ   = ( 33,  38,  47)
C_CELL_HEAD  = ( 22,  27,  34)  # base; el glow lo hace especial
C_CELL_FLASH = ( 56,  68,  42)  # verde oscuro al escribir

# Botones
C_BTN        = ( 33,  38,  50)
C_BTN_HOV    = ( 48,  54,  72)
C_BTN_RUN    = ( 23,  51,  35)
C_BTN_RUN_H  = ( 35,  72,  50)
C_BTN_RST    = ( 51,  23,  23)
C_BTN_RST_H  = ( 72,  35,  35)

# Filas tabla
C_ROW_A      = ( 22,  27,  34)
C_ROW_B      = ( 26,  31,  39)
C_ROW_ACT    = ( 38,  42,  18)

# Colores por simbolo en cinta
SYM_COLORS = {
    "1": C_BLUE,
    "0": C_YELLOW,
    "_": C_TEXT_MUTE,
    "T": C_GREEN,
    "F": C_RED,
    "X": C_PURPLE,
    "Y": C_PINK,
    "A": C_TEAL,
    "B": C_ORANGE,
    "2": (100, 140, 180),
    "3": (140, 100, 160),
    "4": (100, 160, 130),
}

def sym_color(s):
    return SYM_COLORS.get(s, C_TEXT)

def tape_grid_layout():
    """Origen x0 y ancho total del bloque de celdas de la cinta (centrado)."""
    total_w = NUM_CELLS * (CELL_W + GAP) - GAP
    x0 = (WIN_W - total_w) // 2
    return x0, total_w

# ---------------------------------------------------------------------------
# Helpers de dibujo
# ---------------------------------------------------------------------------
def rrect(surf, color, rect, r=8, border=0, border_color=None):
    """Rectangulo con esquinas redondeadas."""
    pygame.draw.rect(surf, color, rect, border_radius=r)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=r)

def hline(surf, color, y, x0=0, x1=None, w=1):
    if x1 is None:
        x1 = WIN_W
    pygame.draw.line(surf, color, (x0, y), (x1, y), w)

def vline(surf, color, x, y0, y1, w=1):
    pygame.draw.line(surf, color, (x, y0), (x, y1), w)

def txt(surf, text, font, color, x, y, anchor="topleft", alpha=255):
    s = font.render(text, True, color)
    if alpha < 255:
        s.set_alpha(alpha)
    r = s.get_rect()
    setattr(r, anchor, (x, y))
    surf.blit(s, r)
    return r

def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def parse_registers(text):
    text = text.strip()
    if not text:
        return []
    parts = text.split()
    result = []
    for p in parts:
        v = int(p)
        if v < 0:
            raise ValueError(f"Registro negativo: {v}")
        result.append(v)
    return result

# ---------------------------------------------------------------------------
# Animaciones simples
# ---------------------------------------------------------------------------
class FlashCell:
    """Un destello verde en una celda de la cinta cuando se escribe."""
    DURATION = 400  # ms

    def __init__(self, tape_index):
        self.index = tape_index
        self.age   = 0

    def update(self, dt):
        self.age += dt

    @property
    def done(self):
        return self.age >= self.DURATION

    @property
    def t(self):
        """0 → 1 conforme avanza."""
        return min(1.0, self.age / self.DURATION)

    def cell_color(self, base):
        # flash verde → base
        return lerp_color(C_CELL_FLASH, base, self.t)


# ---------------------------------------------------------------------------
# Aplicacion principal
# ---------------------------------------------------------------------------
class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Maquina de Turing  ·  Laboratorio")

        # Fuentes
        self.f_title  = pygame.font.SysFont("monospace", 20, bold=True)
        self.f_lg     = pygame.font.SysFont("monospace", 18, bold=True)
        self.f_md     = pygame.font.SysFont("monospace", 15)
        self.f_sm     = pygame.font.SysFont("monospace", 13)
        self.f_xs     = pygame.font.SysFont("monospace", 11)
        self.f_cell   = pygame.font.SysFont("monospace", 26, bold=True)
        self.f_idx    = pygame.font.SysFont("monospace", 9)
        self.f_btn    = pygame.font.SysFont("monospace", 14, bold=True)

        # Estado maquina
        self.tm         = None
        self.tm_error   = None if TM_CLASS_AVAILABLE else TM_IMPORT_ERROR
        self.step_count = 0
        self.running    = False
        self.accumulator = 0
        self.speed      = 5
        self.exec_start_time = None
        self.last_run_duration_sec = None

        # Texto
        self.field_path  = "microcodes/suma.json"
        self.field_regs  = "3 2"
        self.active_field = 0

        # Tabla transiciones
        self.tt_scroll   = 0
        self.tt_rows     = []
        self.tt_active   = -1

        # Desplazamiento horizontal de la vista de la cinta (indices de cinta vs cabezal).
        # La ventana se centra en: get_head_pos() + tape_view_shift
        self.tape_view_shift = 0

        # Animaciones
        self.flashes   = []   # lista de FlashCell
        self.pulse     = 0.0  # 0..2π para glow del cabezal
        self.state_flash_t = 0.0  # 0..1 destello al cambiar de estado
        self.prev_state = ""

        # Botones
        self._build_buttons()

        self.clock = pygame.time.Clock()

    # ------------------------------------------------------------------
    def _build_buttons(self):
        bh   = 38
        by   = Y_CONTROLS + (H_CONTROLS - bh) // 2
        gap  = 12

        bw_step = 150
        bw_run  = 200
        bw_rst  = 150
        total   = bw_step + bw_run + bw_rst + 2 * gap
        x0      = (WIN_W - total) // 2

        self.btn_step  = pygame.Rect(x0,                        by, bw_step, bh)
        self.btn_run   = pygame.Rect(x0 + bw_step + gap,        by, bw_run,  bh)
        self.btn_reset = pygame.Rect(x0 + bw_step + bw_run + 2*gap, by, bw_rst, bh)

        # Boton cargar en panel input
        self.btn_load  = pygame.Rect(WIN_W - 180, Y_INPUT + (H_INPUT - 36) // 2, 148, 36)

        x0, total_w = tape_grid_layout()
        arrow_w, arrow_h = 44, CELL_H + 20
        tape_cy = Y_TAPE + H_TAPE // 2
        gap_ar = 12
        self.btn_tape_left = pygame.Rect(
            x0 - arrow_w - gap_ar, tape_cy - arrow_h // 2, arrow_w, arrow_h)
        self.btn_tape_right = pygame.Rect(
            x0 + total_w + gap_ar, tape_cy - arrow_h // 2, arrow_w, arrow_h)

    # ------------------------------------------------------------------
    # Carga / reset
    # ------------------------------------------------------------------
    def _load_machine(self):
        if not TM_CLASS_AVAILABLE:
            self.tm_error = TM_IMPORT_ERROR
            return
        path = self.field_path.strip()
        try:
            regs = parse_registers(self.field_regs)
        except ValueError as e:
            self.tm_error = f"Registros invalidos: {e}"
            return
        try:
            self.tm = TuringMachine(path, regs)
            self.tm_error  = None
            self.step_count = 0
            self.running    = False
            self.accumulator = 0
            self.exec_start_time = None
            self.last_run_duration_sec = None
            self.tt_scroll  = 0
            self.tape_view_shift = 0
            self.flashes    = []
            self.prev_state = self._safe_get_state()
            self._rebuild_tt()
        except FileNotFoundError:
            self.tm = None
            self.tm_error = f"Archivo no encontrado: {path}"
        except json.JSONDecodeError as e:
            self.tm = None
            self.tm_error = f"JSON invalido: {e}"
        except NotImplementedError:
            self.tm = None
            self.tm_error = "NotImplementedError en __init__ — implementa la clase primero"
        except Exception as e:
            self.tm = None
            self.tm_error = f"{type(e).__name__}: {e}"

    def _rebuild_tt(self):
        self.tt_rows = []
        if self.tm is None:
            return
        try:
            transitions = self.tm.config.get("transitions", {})
        except Exception:
            return
        for state, syms in transitions.items():
            for sym, action in syms.items():
                self.tt_rows.append((
                    state,
                    sym,
                    action.get("write", "?"),
                    action.get("move", "?"),
                    action.get("next_state", "?"),
                ))

    def _do_step(self):
        if self.tm is None or self._safe_is_halted():
            self.running = False
            return
        try:
            prev_state = self._safe_get_state()
            head_before = self._safe_get_head()
            self.tm.step()
            self.step_count += 1
            self._update_tt_active()
            # Flash en celda escrita (posicion anterior al movimiento)
            lt = self._safe_get_last()
            if lt:
                self.flashes.append(FlashCell(head_before))
                # Destello de estado
                new_state = self._safe_get_state()
                if new_state != prev_state:
                    self.state_flash_t = 1.0
                    self.prev_state = new_state
        except NotImplementedError:
            self.tm_error = "step() aun no implementado"
            self.running = False
            self.exec_start_time = None
        except Exception as e:
            self.tm_error = f"Error en step(): {type(e).__name__}: {e}"
            self.running = False
            self.exec_start_time = None

    def _update_tt_active(self):
        try:
            lt = self.tm.get_last_transition()
            if not lt:
                self.tt_active = -1
                return
            fs, sr = lt.get("from_state"), lt.get("symbol_read")
            for i, row in enumerate(self.tt_rows):
                if row[0] == fs and row[1] == sr:
                    self.tt_active = i
                    visible = (H_TTABLE - 44) // 22
                    if i < self.tt_scroll:
                        self.tt_scroll = i
                    elif i >= self.tt_scroll + visible:
                        self.tt_scroll = i - visible + 1
                    return
        except Exception:
            pass
        self.tt_active = -1

    # ------------------------------------------------------------------
    # Safe helpers
    # ------------------------------------------------------------------
    def _safe_is_halted(self):
        try:
            return self.tm.is_halted()
        except Exception:
            return True

    def _safe_get_state(self):
        try:
            return self.tm.get_state()
        except Exception:
            return "?"

    def _safe_get_head(self):
        try:
            return self.tm.get_head_pos()
        except Exception:
            return 0

    def _safe_get_window(self):
        try:
            center = self._safe_get_head() + self.tape_view_shift
            return self.tm.get_tape_window(center, NUM_CELLS)
        except Exception:
            return ["?"] * NUM_CELLS

    def _safe_get_last(self):
        try:
            return self.tm.get_last_transition()
        except Exception:
            return {}

    def _finish_run_timing(self):
        if self.exec_start_time is not None:
            self.last_run_duration_sec = time.perf_counter() - self.exec_start_time
            self.exec_start_time = None

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.MOUSEWHEEL:
                max_s = max(0, len(self.tt_rows) - 1)
                self.tt_scroll = max(0, min(max_s, self.tt_scroll - event.y))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Campos de texto
                if pygame.Rect(20, Y_INPUT + 22, 500, 32).collidepoint(mx, my):
                    self.active_field = 0
                    # Si el usuario edita, no mostramos errores viejos hasta que cargue.
                    self.tm_error = None
                elif pygame.Rect(540, Y_INPUT + 22, 280, 32).collidepoint(mx, my):
                    self.active_field = 1
                    # Si el usuario edita, no mostramos errores viejos hasta que cargue.
                    self.tm_error = None
                # Botones
                elif self.btn_load.collidepoint(mx, my):
                    self._load_machine()
                elif self.btn_step.collidepoint(mx, my) and not self.running:
                    self._do_step()
                elif self.btn_run.collidepoint(mx, my):
                    if self.tm and not self._safe_is_halted():
                        self.running = not self.running
                        self.accumulator = 0
                        if self.running:
                            self.exec_start_time = time.perf_counter()
                        else:
                            self.exec_start_time = None
                elif self.btn_reset.collidepoint(mx, my):
                    self._load_machine()
                elif self.tm is not None and self.btn_tape_left.collidepoint(mx, my):
                    self.tape_view_shift -= 1
                elif self.tm is not None and self.btn_tape_right.collidepoint(mx, my):
                    self.tape_view_shift += 1

            elif event.type == pygame.KEYDOWN:
                # Tab/Enter siempre funcionan, incluso editando campos.
                if event.key == pygame.K_TAB:
                    self.active_field = 1 - self.active_field
                    self.tm_error = None
                    continue
                if event.key == pygame.K_RETURN:
                    self._load_machine()
                    continue

                # Si el usuario está editando un campo, priorizamos la entrada de texto
                # y desactivamos atajos (R/F/Espacio/↑/↓) para no “comerse” letras.
                if self.active_field in (0, 1):
                    ch = event.unicode
                    if event.key == pygame.K_BACKSPACE:
                        if self.active_field == 0:
                            self.field_path = self.field_path[:-1]
                        else:
                            self.field_regs = self.field_regs[:-1]
                        self.tm_error = None
                    elif event.key == pygame.K_SPACE and self.active_field == 1:
                        # En "Registros", el espacio es separador válido.
                        self.field_regs += " "
                        self.tm_error = None
                    elif ch and ch.isprintable():
                        if self.active_field == 0:
                            self.field_path += ch
                        else:
                            self.field_regs += ch
                        self.tm_error = None
                    continue

                # Atajos (solo cuando NO estás escribiendo en los campos)
                if event.key == pygame.K_f:
                    if self.tm and not self.running and not self._safe_is_halted():
                        self._do_step()
                elif event.key == pygame.K_SPACE:
                    if self.tm and not self._safe_is_halted():
                        self.running = not self.running
                        self.accumulator = 0
                        if self.running:
                            self.exec_start_time = time.perf_counter()
                        else:
                            self.exec_start_time = None
                elif event.key == pygame.K_r:
                    self._load_machine()
                elif event.key == pygame.K_UP:
                    self.speed = min(10, self.speed + 1)
                elif event.key == pygame.K_DOWN:
                    self.speed = max(1, self.speed - 1)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    SPEED_DELAYS = [2000, 1000, 600, 350, 200, 120, 70, 40, 25, 16]

    def update(self, dt):
        # Animaciones
        self.pulse += dt * 0.004  # ciclo ~1.5s
        self.state_flash_t = max(0.0, self.state_flash_t - dt / 400)
        for f in self.flashes:
            f.update(dt)
        self.flashes = [f for f in self.flashes if not f.done]

        # Auto-run
        if self.running and self.tm and not self._safe_is_halted():
            self.accumulator += dt
            delay = self.SPEED_DELAYS[self.speed - 1]
            if self.accumulator >= delay:
                self.accumulator = 0
                self._do_step()
                if self._safe_is_halted():
                    self._finish_run_timing()
                    self.running = False
        elif self.running and self._safe_is_halted():
            self._finish_run_timing()
            self.running = False

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def draw(self):
        self.screen.fill(C_BG)
        self._draw_header()
        self._draw_input()
        self._draw_status()
        self._draw_tape()
        self._draw_controls()
        self._draw_table()
        pygame.display.flip()

    # --- Header -------------------------------------------------------
    def _draw_header(self):
        pygame.draw.rect(self.screen, C_SURFACE, (0, 0, WIN_W, H_HEADER))
        hline(self.screen, C_BORDER, H_HEADER - 1)

        txt(self.screen, "MAQUINA DE TURING", self.f_title, C_TEXT,
            WIN_W // 2, H_HEADER // 2, anchor="center")

        # Indicador de estado running
        if self.running:
            dot_col = C_GREEN
            dot_txt = "EJECUTANDO"
        elif self.tm and self._safe_is_halted():
            dot_col = C_RED
            dot_txt = "DETENIDA"
        elif self.tm:
            dot_col = C_YELLOW
            dot_txt = "EN PAUSA"
        else:
            dot_col = C_TEXT_DIM
            dot_txt = "SIN CARGA"

        rx = WIN_W - 20
        txt(self.screen, dot_txt, self.f_xs, dot_col, rx, H_HEADER // 2, anchor="midright")
        pygame.draw.circle(self.screen, dot_col,
                           (rx - self.f_xs.size(dot_txt)[0] - 12, H_HEADER // 2), 4)

    # --- Input --------------------------------------------------------
    def _draw_input(self):
        pygame.draw.rect(self.screen, C_SURFACE2, (0, Y_INPUT, WIN_W, H_INPUT))
        hline(self.screen, C_BORDER, Y_INPUT + H_INPUT - 1)

        if not TM_CLASS_AVAILABLE:
            msg = f"  ERROR DE IMPORTACION: {TM_IMPORT_ERROR[:80]}"
            rrect(self.screen, (51, 20, 20),
                  pygame.Rect(16, Y_INPUT + 16, WIN_W - 32, H_INPUT - 32), r=6)
            txt(self.screen, msg, self.f_sm, C_RED,
                WIN_W // 2, Y_INPUT + H_INPUT // 2, anchor="center")
            return

        cy = Y_INPUT + H_INPUT // 2

        # Campo path
        txt(self.screen, "JSON", self.f_xs, C_TEXT_DIM, 20, cy - 22)
        r0 = pygame.Rect(20, cy - 10, 490, 30)
        bc0 = C_BLUE if self.active_field == 0 else C_BORDER
        rrect(self.screen, C_SURFACE, r0, r=5, border=1, border_color=bc0)
        # Cursor parpadeante
        display_path = self.field_path
        if self.active_field == 0 and int(pygame.time.get_ticks() / 500) % 2 == 0:
            display_path += "|"
        txt(self.screen, display_path, self.f_md, C_TEXT, r0.left + 8, r0.centery, anchor="midleft")

        # Campo registros
        txt(self.screen, "Registros", self.f_xs, C_TEXT_DIM, 526, cy - 22)
        r1 = pygame.Rect(526, cy - 10, 240, 30)
        bc1 = C_BLUE if self.active_field == 1 else C_BORDER
        rrect(self.screen, C_SURFACE, r1, r=5, border=1, border_color=bc1)
        display_regs = self.field_regs
        if self.active_field == 1 and int(pygame.time.get_ticks() / 500) % 2 == 0:
            display_regs += "|"
        txt(self.screen, display_regs, self.f_md, C_TEXT, r1.left + 8, r1.centery, anchor="midleft")

        # Boton cargar
        mx, my = pygame.mouse.get_pos()
        hov = self.btn_load.collidepoint(mx, my)
        bc = C_BTN_HOV if hov else C_BTN
        rrect(self.screen, bc, self.btn_load, r=6, border=1,
              border_color=C_BLUE if hov else C_BORDER)
        txt(self.screen, "Cargar  [Enter]", self.f_btn, C_BLUE if hov else C_TEXT,
            self.btn_load.centerx, self.btn_load.centery, anchor="center")

        # Mensaje error/ok bajo los campos
        if self.tm_error:
            short = self.tm_error[:95]
            txt(self.screen, f"  {short}", self.f_xs, C_RED,
                20, Y_INPUT + H_INPUT - 3, anchor="bottomleft")
        elif self.tm is not None:
            txt(self.screen, "  Maquina cargada", self.f_xs, C_GREEN,
                20, Y_INPUT + H_INPUT - 3, anchor="bottomleft")

    # --- Status bar ---------------------------------------------------
    def _draw_status(self):
        pygame.draw.rect(self.screen, C_SURFACE, (0, Y_STATUS, WIN_W, H_STATUS))
        hline(self.screen, C_BORDER, Y_STATUS + H_STATUS - 1)

        cy = Y_STATUS + H_STATUS // 2

        if self.tm is None:
            txt(self.screen,
                "Escribe la ruta del archivo JSON y los registros, luego presiona Enter",
                self.f_sm, C_TEXT_DIM, WIN_W // 2, cy, anchor="center")
            return

        halted  = self._safe_is_halted()
        state   = self._safe_get_state()
        state_c = C_RED if halted else lerp_color(C_BLUE, C_TEAL, self.state_flash_t)

        # Estado
        txt(self.screen, "ESTADO", self.f_xs, C_TEXT_DIM, 24, cy - 12)
        txt(self.screen, state, self.f_lg, state_c, 24, cy + 2)

        vline(self.screen, C_BORDER, 200, Y_STATUS + 10, Y_STATUS + H_STATUS - 10)

        # Paso
        txt(self.screen, "PASO", self.f_xs, C_TEXT_DIM, 216, cy - 12)
        txt(self.screen, str(self.step_count), self.f_lg, C_TEXT, 216, cy + 2)

        vline(self.screen, C_BORDER, 360, Y_STATUS + 10, Y_STATUS + H_STATUS - 10)

        # Ultima transicion
        lt = self._safe_get_last()
        if lt:
            tr_txt = (f"({lt.get('from_state','?')}, '{lt.get('symbol_read','?')}')  →  "
                      f"{lt.get('to_state','?')}  |  escribe '{lt.get('wrote','?')}'  |  "
                      f"mueve {lt.get('moved','?')}")
        else:
            tr_txt = "—"
        txt(self.screen, "ULTIMA TRANSICION", self.f_xs, C_TEXT_DIM, 376, cy - 12)
        txt(self.screen, tr_txt[:62], self.f_sm, C_YELLOW, 376, cy + 2)

        # HALT badge
        if halted:
            bw = 90
            br = pygame.Rect(WIN_W - bw - 20, cy - 14, bw, 28)
            rrect(self.screen, (51, 20, 20), br, r=14)
            pygame.draw.rect(self.screen, C_RED, br, 1, border_radius=14)
            txt(self.screen, "HALT", self.f_btn, C_RED, br.centerx, br.centery, anchor="center")

    # --- Tape ---------------------------------------------------------
    def _draw_tape(self):
        pygame.draw.rect(self.screen, C_BG, (0, Y_TAPE, WIN_W, H_TAPE))

        # Rail de fondo
        rail_h = CELL_H + 20
        rail_y = Y_TAPE + (H_TAPE - rail_h) // 2
        pygame.draw.rect(self.screen, C_SURFACE, (0, rail_y, WIN_W, rail_h))

        x0, total_w = tape_grid_layout()
        cy = Y_TAPE + H_TAPE // 2

        mid = NUM_CELLS // 2  # centro de la ventana (indice de columna)

        if self.tm is None:
            head = 0
            tape_center = 0
            i_head = mid
        else:
            head = self._safe_get_head()
            tape_center = head + self.tape_view_shift
            # Columna donde se dibuja el cabezal real (puede salir del rango visible)
            i_head = mid - self.tape_view_shift

            # Glow bajo la celda del cabezal
            glow_alpha = int(60 + 40 * math.sin(self.pulse))
            glow_w, glow_h = CELL_W + 20, CELL_H + 20
            glow_x = x0 + i_head * (CELL_W + GAP) - 10
            glow_y = cy - CELL_H // 2 - 10
            glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
            glow_col  = (*C_BLUE, glow_alpha)
            pygame.draw.rect(glow_surf, glow_col, (0, 0, glow_w, glow_h), border_radius=12)
            self.screen.blit(glow_surf, (glow_x, glow_y))

        if self.tm is None:
            # Celdas vacias decorativas
            for i in range(NUM_CELLS):
                x = x0 + i * (CELL_W + GAP)
                r = pygame.Rect(x, cy - CELL_H // 2, CELL_W, CELL_H)
                bg = C_CELL_ADJ if abs(i - mid) <= 1 else C_CELL_BG
                rrect(self.screen, bg, r, r=8)
            self._draw_tape_arrows(disabled=True)
            return

        window = self._safe_get_window()

        # Construir mapa de flash por indice de cinta
        flash_map = {}
        for f in self.flashes:
            flash_map[f.index] = f

        for i, sym in enumerate(window):
            tape_idx = tape_center - mid + i
            x = x0 + i * (CELL_W + GAP)
            r = pygame.Rect(x, cy - CELL_H // 2, CELL_W, CELL_H)

            is_head = (tape_idx == head)
            is_adj  = False
            if self.tm is not None:
                # adyacente al cabezal en indices de cinta (vista desplazada)
                is_adj = (not is_head) and abs(tape_idx - head) == 1

            # Fondo
            if tape_idx in flash_map:
                bg = flash_map[tape_idx].cell_color(
                    C_CELL_HEAD if is_head else (C_CELL_ADJ if is_adj else C_CELL_BG))
            else:
                if is_head:
                    bg = C_CELL_HEAD
                elif is_adj:
                    bg = C_CELL_ADJ
                else:
                    bg = C_CELL_BG

            # Borde
            if is_head:
                border_c = C_BLUE
                br_w = 2
            elif is_adj:
                border_c = C_BORDER_LT
                br_w = 1
            else:
                border_c = C_BORDER
                br_w = 1

            rrect(self.screen, bg, r, r=8, border=br_w, border_color=border_c)

            # Simbolo
            sc = sym_color(sym)
            txt(self.screen, sym, self.f_cell, sc, r.centerx, r.centery, anchor="center")

            # Indice
            idx_col = C_BLUE if is_head else C_TEXT_MUTE
            txt(self.screen, str(tape_idx), self.f_idx, idx_col,
                r.left + 3, r.top + 3)

        # Triangulo / indicador cabezal (sigue al cabezal aunque la vista este desplazada)
        head_cx = x0 + i_head * (CELL_W + GAP) + CELL_W // 2
        tri_y   = cy - CELL_H // 2 - 14
        pygame.draw.polygon(self.screen, C_BLUE, [
            (head_cx, tri_y + 10),
            (head_cx - 7, tri_y),
            (head_cx + 7, tri_y),
        ])

        # Etiqueta "CABEZAL"
        txt(self.screen, "CABEZAL", self.f_idx, C_BLUE,
            head_cx, tri_y - 2, anchor="midbottom")

        self._draw_tape_arrows(disabled=False)

    def _draw_tape_arrows(self, disabled):
        """Botones ◀ ▶ junto a la cinta para pan horizontal."""
        mx, my = pygame.mouse.get_pos()

        def one(rect, label):
            hov = rect.collidepoint(mx, my) and not disabled
            base = (40, 44, 52) if disabled else C_BTN
            hov_c = C_BTN_HOV if not disabled else base
            col = hov_c if hov else base
            tc = C_TEXT_MUTE if disabled else (C_TEXT if hov else C_TEXT_DIM)
            rrect(self.screen, col, rect, r=7, border=1,
                  border_color=C_BORDER_LT if hov and not disabled else C_BORDER)
            txt(self.screen, label, self.f_btn, tc,
                rect.centerx, rect.centery, anchor="center")

        one(self.btn_tape_left, "\u25c0")
        one(self.btn_tape_right, "\u25b6")

    # --- Controles ----------------------------------------------------
    def _draw_controls(self):
        pygame.draw.rect(self.screen, C_SURFACE2, (0, Y_CONTROLS, WIN_W, H_CONTROLS))
        hline(self.screen, C_BORDER, Y_CONTROLS)
        hline(self.screen, C_BORDER, Y_CONTROLS + H_CONTROLS - 1)

        mx, my = pygame.mouse.get_pos()
        halted = self.tm is None or self._safe_is_halted()
        cy_ctrl = Y_CONTROLS + H_CONTROLS // 2

        def draw_btn(rect, label, base, hov_c, disabled=False):
            hov = rect.collidepoint(mx, my) and not disabled
            col = (28, 33, 40) if disabled else (hov_c if hov else base)
            tc  = C_TEXT_MUTE if disabled else (C_TEXT if hov else (200, 210, 220))
            rrect(self.screen, col, rect, r=7, border=1,
                  border_color=C_BORDER_LT if hov and not disabled else C_BORDER)
            txt(self.screen, label, self.f_btn, tc,
                rect.centerx, rect.centery, anchor="center")

        draw_btn(self.btn_step,  "Paso  [F]",
                 C_BTN, C_BTN_HOV, disabled=(halted or self.running))

        if self.last_run_duration_sec is not None:
            tmsg = f"Tiempo ejecución: {self.last_run_duration_sec:.3f} s"
            txt(self.screen, tmsg, self.f_sm, C_TEAL,
                self.btn_step.left - 10, cy_ctrl, anchor="midright")

        if self.running:
            draw_btn(self.btn_run, "Pausar  [Espacio]",
                     C_BTN_RUN, C_BTN_RUN_H, disabled=halted)
        else:
            draw_btn(self.btn_run, "Ejecutar  [Espacio]",
                     C_BTN, C_BTN_HOV, disabled=halted)

        draw_btn(self.btn_reset, "Reiniciar  [R]", C_BTN_RST, C_BTN_RST_H)

        # Velocidad
        vx = WIN_W - 24
        vy = Y_CONTROLS + H_CONTROLS // 2
        txt(self.screen, f"Vel. {self.speed}/10  [↑ ↓]",
            self.f_sm, C_TEXT_DIM, vx, vy, anchor="midright")
        # Barrita de velocidad
        bar_w = 100
        bar_x = vx - self.f_sm.size(f"Vel. {self.speed}/10  [↑ ↓]")[0] - 16
        bar_y = vy
        pygame.draw.rect(self.screen, C_BORDER,
                         (bar_x - bar_w, bar_y - 3, bar_w, 6), border_radius=3)
        fill = int(bar_w * self.speed / 10)
        pygame.draw.rect(self.screen, C_BLUE,
                         (bar_x - bar_w, bar_y - 3, fill, 6), border_radius=3)

    # --- Tabla de transiciones ----------------------------------------
    def _draw_table(self):
        pygame.draw.rect(self.screen, C_SURFACE, (0, Y_TTABLE, WIN_W, H_TTABLE))
        hline(self.screen, C_BORDER, Y_TTABLE)

        # Header
        header_y = Y_TTABLE + 8
        txt(self.screen, "TABLA DE TRANSICIONES", self.f_xs, C_TEXT_DIM,
            WIN_W // 2, header_y, anchor="center")

        # Columnas
        COL_X = [32, 230, 420, 600, 760]
        HEADERS = ["Estado Actual", "Lee", "Escribe", "Mueve", "Siguiente Estado"]
        col_y = header_y + 16
        for cx, ch in zip(COL_X, HEADERS):
            txt(self.screen, ch, self.f_xs, C_TEXT_DIM, cx, col_y)
        hline(self.screen, C_BORDER, col_y + 16, x0=16, x1=WIN_W - 16)

        if not self.tt_rows:
            txt(self.screen,
                "[ Carga un archivo JSON para ver las transiciones ]",
                self.f_sm, C_TEXT_MUTE, WIN_W // 2,
                Y_TTABLE + H_TTABLE // 2, anchor="center")
            return

        row_h   = 22
        start_y = col_y + 20
        visible = (WIN_H - start_y - 4) // row_h

        for i, row in enumerate(self.tt_rows[self.tt_scroll:self.tt_scroll + visible]):
            ai  = i + self.tt_scroll
            ry  = start_y + i * row_h
            is_active = (ai == self.tt_active)

            bg = C_ROW_ACT if is_active else (C_ROW_B if i % 2 else C_ROW_A)
            pygame.draw.rect(self.screen, bg, (16, ry, WIN_W - 32, row_h - 1))

            # Borde izquierdo para fila activa
            if is_active:
                pygame.draw.rect(self.screen, C_TEAL, (16, ry, 3, row_h - 1))

            tc = C_TEAL if is_active else C_TEXT
            for cx, val in zip(COL_X, row):
                txt(self.screen, str(val), self.f_sm, tc, cx, ry + 3)

        # Scroll bar
        if len(self.tt_rows) > visible and visible > 0:
            bar_x  = WIN_W - 8
            bar_y0 = start_y
            bar_h  = WIN_H - start_y - 4
            thumb_h = max(20, bar_h * visible // len(self.tt_rows))
            thumb_y = bar_y0 + bar_h * self.tt_scroll // len(self.tt_rows)
            pygame.draw.rect(self.screen, C_SURFACE2, (bar_x, bar_y0, 4, bar_h), border_radius=2)
            pygame.draw.rect(self.screen, C_BORDER_LT, (bar_x, thumb_y, 4, thumb_h), border_radius=2)

    # ------------------------------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(60)
            self.handle_events()
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    app = App()
    app.run()
