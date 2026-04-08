#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejecuta la Maquina de Turing en terminal (sin interfaz grafica).

Desde esta carpeta:
  python run_tm.py microcodes/suma.json 3 2
  python run_tm.py microcodes/suma.json
  python run_tm.py microcodes/resta_lr.json 5 3 --max-steps 5000

Requiere tener implementada la clase TuringMachine en turing_machine.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
REPO = LAB.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(LAB))

from tm_terminal_common import parse_registers, run_machine  # noqa: E402
from turing_machine import TuringMachine  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(
        description="Simulador de MT en terminal: muestra cada paso y el estado final."
    )
    p.add_argument(
        "json",
        type=str,
        help="Ruta al microcodigo JSON (ej. microcodes/suma.json)",
    )
    p.add_argument(
        "registers",
        nargs="*",
        help="Registros en unario: enteros separados por espacio (ej. 3 2)",
    )
    p.add_argument(
        "--max-steps",
        type=int,
        default=1_000_000,
        metavar="N",
        help="Limite de pasos (por defecto 1000000)",
    )
    args = p.parse_args()

    json_path = Path(args.json)
    if not json_path.is_file():
        print(f"Error: no existe el archivo: {json_path.resolve()}", file=sys.stderr)
        return 1

    regs = parse_registers(args.registers)
    print(f"Archivo: {json_path.resolve()}")
    print(f"Registros: {regs}")
    print()

    return run_machine(TuringMachine, str(json_path.resolve()), regs, args.max_steps)


if __name__ == "__main__":
    raise SystemExit(main())
