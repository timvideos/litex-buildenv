#!/usr/bin/env python3
"""
Copyright (c) 2019 Antmicro

Renode platform definition (repl) and script (resc) generator for LiteX SoC.

This script parses LiteX 'csr.csv' file and generates scripts for Renode
necessary to emulate the given configuration of the LiteX SoC.
"""

import sys
import csv
import argparse

# this memory region is defined and handled
# directly by LiteEth model in Renode
non_generated_mem_regions = ['ethmac']

mem_regions = {}
peripherals = {}
constants = {}

def generate_ethmac(peripheral, **kwargs):
    """ Generates definition of 'ethmac' peripheral.

    Args:
        peripheral (dict): peripheral description
        kwargs (dict): additional parameters, including 'buffer'

    Returns:
        string: repl definition of the peripheral
    """
    buf = kwargs['buffer']()

    result = """
ethmac: Network.LiteX_Ethernet @ {{
    sysbus <{}, +0x100>;
    sysbus new Bus.BusMultiRegistration {{ address: {}; size: {}; region: "buffer" }}
}}
""".format(peripheral['address'], buf['address'], buf['size'])

    if 'interrupt' in peripheral['constants']:
        result += '    -> cpu@{}\n'.format(peripheral['constants']['interrupt'])

    return result

def generate_memory_region(region_descriptor):
    """ Generates definition of memory region.

    Args:
        region_descriptor (dict): memory region description

    Returns:
        string: repl definition of the memory region
    """

    return """
{}: Memory.MappedMemory @ sysbus {}
    size: {}
""".format(region_descriptor['name'], region_descriptor['address'], region_descriptor['size'])

def generate_silencer(peripheral, **kwargs):
    """ Silences access to a memory region.

    Args:
        peripheral (dict): peripheral description
        kwargs (dict): additional parameters, not used

    Returns:
        string: repl definition of the silencer
    """
    return """
sysbus:
    init add:
        SilenceRange <{} 0x200> # {}
""".format(peripheral['address'], peripheral['name'])

def generate_cpu():
    """ Generates definition of a CPU.

    Returns:
        string: repl definition of the CPU
    """
    kind = constants['config_cpu_type']['value']

    if kind == 'VEXRISCV':
        return """
cpu: CPU.VexRiscv @ sysbus
"""
    elif kind == 'PICORV32':
        return """
cpu: CPU.PicoRV32 @ sysbus
    cpuType: "rv32imc"
"""
    else:
        raise Exception('Unsupported cpu type: {}'.format(kind))

def generate_peripheral(peripheral, **kwargs):
    """ Generates definition of a peripheral.

    Args:
        peripheral (dict): peripheral description
        kwargs (dict): additional parameters, including 'model' and 'properties'

    Returns:
        string: repl definition of the peripheral
    """
    result = '\n{}: {} @ sysbus {}\n'.format(
        peripheral['name'],
        kwargs['model'],
        peripheral['address'])

    for constant, val in peripheral['constants'].items():
        if constant == 'interrupt':
            result += '    -> cpu@{}\n'.format(val)
        else:
            result += '    {}: {}\n'.format(constant, val)

    if 'properties' in kwargs:
        for prop, val in kwargs['properties'].items():
            result += '    {}: {}\n'.format(prop, val())

    return result

def generate_repl():
    """ Generates platform definition.

    Returns:
        string: platform defition containing all supported peripherals and memory regions
    """
    result = ""

    # defines mapping of LiteX peripherals to Renode models
    name_to_handler = {
        'uart': {
            'handler': generate_peripheral,
            'model': 'UART.LiteX_UART'
        },
        'timer0': {
            'handler': generate_peripheral,
            'model': 'Timers.LiteX_Timer',
            'properties': {
                'frequency': lambda: constants['system_clock_frequency']['value']
            }
        },
        'ethmac': {
            'handler': generate_ethmac,
            'buffer': lambda: mem_regions['ethmac']
        },
        'ddrphy': {
            'handler': generate_silencer
        },
        'sdram': {
            'handler': generate_silencer
        },
        'ethphy': {
            'handler': generate_silencer
        }
    }

    for mem_region in mem_regions.values():
        if mem_region['name'] not in non_generated_mem_regions:
            result += generate_memory_region(mem_region)

    result += generate_cpu()

    for name, peripheral in peripherals.items():
        if name not in name_to_handler:
            print('Skipping unsupported peripheral {} at {}'.format(name, peripheral['address']))
            continue

        h = name_to_handler[name]
        result += h['handler'](peripheral, **h)

    return result

def parse_csv(data):
    """ Parses LiteX CSV file.

    Args:
        data (list): list of CSV file lines
    """

    # scan for CSRs first, so it's easier to resolve CSR-related constants in the second pass
    for _type, _name, _address, _, __ in data:
        if _type == 'csr_base':
            peripherals[_name] = {'name': _name, 'address': _address, 'constants': {}}

    for _type, _name, _val, _val2, _ in data:
        if _type == 'csr_base':
            # CSRs have already been parsed
            pass
        elif _type == 'csr_register':
            # we are currently not interested in this
            pass
        elif _type == 'constant':
            found = False
            for _csr_name in peripherals:
                if _name.startswith(_csr_name):
                    peripherals[_csr_name]['constants'][_name[len(_csr_name)+1:]] = _val
                    found = True
                    break
            if not found:
                # if it's not a CSR-related constant, it must be a global one
                constants[_name] = {'name': _name, 'value': _val}
        elif _type == 'memory_region':
            mem_regions[_name] = {'name': _name, 'address': _val, 'size': _val2}
        else:
            print('Skipping unexpected CSV entry: {} {}'.format(_type, _name))

def generate_resc(repl_file, host_tap_interface=None, bios_binary=None):
    """ Generates platform definition.

    Args:
        repl_file (string): path to Renode platform definition file
        host_tap_interface (string): name of the tap interface on host machine or None if no network should be configured
        bios_binary (string): path to the binary file of LiteX BIOS or None if it should not be loaded into ROM

    Returns:
        string: platform defition containing all supported peripherals and memory regions
    """
    cpu_type = constants['config_cpu_type']['value']

    result = """
using sysbus
mach create "litex-{}"
machine LoadPlatformDescription @{}
cpu StartGdbServer 10001
showAnalyzer sysbus.uart
showAnalyzer sysbus.uart Antmicro.Renode.Analyzers.LoggingUartAnalyzer
""".format(cpu_type, repl_file)

    rom_base = mem_regions['rom']['address']
    if rom_base is not None and bios_binary:
        # load LiteX BIOS to ROM
        result += """
sysbus LoadBinary @{} {}
cpu PC {}
""".format(bios_binary, rom_base, rom_base)

    if host_tap_interface:
        # configure network to allow netboot
        result += """
emulation CreateSwitch "switch"
emulation CreateTap "{}" "tap"
connector Connect ethmac switch
connector Connect host.tap switch
""".format(host_tap_interface)

    result += 'start'
    return result

def print_or_save(filepath, lines):
    """ Prints given string on standard output or to the file.

    Args:
        filepath (string): path to the file lines should be written to or '-' to write to a standard output
        lines (string): content to be printed/written
    """
    if filepath == '-':
        print(lines)
    else:
        with open(filepath, 'w') as f:
            f.write(lines)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('conf_file', help='CSV configuration generated by LiteX')
    parser.add_argument('--resc', action='store', help='Output script file')
    parser.add_argument('--repl', action='store', help='Output platform definition file')
    parser.add_argument('--configure-network', action='store', help='Generate virtual network and connect it with host interface')
    parser.add_argument('--bios-binary', action='store', help='Path to the BIOS binary')
    args = parser.parse_args()

    with open(args.conf_file) as csvfile:
        parse_csv(list(csv.reader(csvfile)))

    if args.repl:
        print_or_save(args.repl, generate_repl())

    if args.resc:
        if not args.repl:
            print("In order to generate RESC file you need to generated REPL as well!")
            sys.exit(1)
        else:
            print_or_save(args.resc, generate_resc(args.repl, args.configure_network, args.bios_binary))

