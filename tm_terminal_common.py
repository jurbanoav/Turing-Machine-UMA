import sys
from turing_machine import TuringMachine

def parse_registers(registers):
    if isinstance(registers, list):
        return [int(x) for x in registers]
    return [int(x) for x in str(registers).split()]

def run_machine(machine_class, json_path, regs_list, max_steps=1000):
    """
    Versión final: Pasa los registros directamente al crear la máquina.
    """
    machine = machine_class(json_path, registers=regs_list)

    steps = 0
    print(f"\n--- Iniciando Simulación ---")
    
    while not machine.is_halted() and steps < max_steps:
        machine.step()
        steps += 1
        
    print(f"Estado final:  {machine.state}")
    print(f"Pasos totales: {steps}")
    
    resultado_limpio = "".join(machine.tape).strip(machine.blank)
    print(f"Cinta final:   {resultado_limpio}")
    print(f"Resultado:     {len(resultado_limpio)}")
    print(f"----------------------------\n")