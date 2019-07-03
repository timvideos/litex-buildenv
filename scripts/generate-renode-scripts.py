#!/usr/bin/env python3
"""
Copyright (c) 2019 Antmicro

Renode platform definition (repl) and script (resc) generator for LiteX SoC.

This script parses LiteX 'csr.csv' file and generates scripts for Renode
necessary to emulate the given configuration of the LiteX SoC.
"""

import sys
import csv
import zlib
import argparse

# this memory region is defined and handled
# directly by LiteEth model in Renode
non_generated_mem_regions = ['ethmac', 'spiflash']

mem_regions = {}
peripherals = {}
constants = {}

def generate_sysbus_registration(address, shadow_base, size=None,
                                 skip_braces=False, region=None):
    """ Generates system bus registration information
    consisting of base aaddress and optional shadow
    address.

    Args:
        address (int): peripheral's base address
        shadow_base (int or None): shadow base address
        size (int or None): peripheral's size, if None the value provided
                            by the peripheral in runtime is taken
        skip_braces (bool): determines if the registration info should
                            be put in braces
        region (str or None): name of the region, if None the default
                              one is assumed

    Returns:
        string: registration information
    """

    def generate_registration_entry(address, size=None, name=None):
        if name:
            if not size:
                raise Exception('Size must be provided when registering non-default region')
            return 'sysbus new Bus.BusMultiRegistration {{ address: {}; size: {}; region: "{}" }}'.format(hex(address), hex(size), name)
        if size:
            return "sysbus <{}, +{}>".format(hex(address), hex(size))
        return "sysbus {}".format(hex(address))

    if shadow_base:
        shadowed_address = address | int(shadow_base, 0)

        if shadowed_address == address:
            address &= ~int(shadow_base, 0)

        result = "{}; {}".format(
            generate_registration_entry(address, size, region),
            generate_registration_entry(shadowed_address, size, region))
    else:
        result = generate_registration_entry(address, size, region)

    if not skip_braces:
        result = "{{ {} }}".format(result)

    return result


def generate_ethmac(peripheral, shadow_base, **kwargs):
    """ Generates definition of 'ethmac' peripheral.

    Args:
        peripheral (dict): peripheral description
        shadow_base (int or None): shadow base address
        kwargs (dict): additional parameters, including 'buffer'

    Returns:
        string: repl definition of the peripheral
    """
    buf = kwargs['buffer']()

    result = """
ethmac: Network.LiteX_Ethernet @ {{
    {};
    {}
}}
""".format(generate_sysbus_registration(int(peripheral['address'], 0),
                                        shadow_base,
                                        0x100,
                                        skip_braces=True),
           generate_sysbus_registration(int(buf['address'], 0),
                                        shadow_base,
                                        int(buf['size'], 0),
                                        skip_braces=True, region='buffer'))

    if 'interrupt' in peripheral['constants']:
        result += '    -> cpu@{}\n'.format(
                peripheral['constants']['interrupt'])

    return result

def generate_memory_region(region_descriptor, shadow_base):
    """ Generates definition of memory region.

    Args:
        region_descriptor (dict): memory region description
        shadow_base (int or None): shadow base address

    Returns:
        string: repl definition of the memory region
    """

    return """
{}: Memory.MappedMemory @ {}
    size: {}
""".format(region_descriptor['name'],
           generate_sysbus_registration(int(region_descriptor['address'], 0),
                                        shadow_base),
           region_descriptor['size'])

def generate_silencer(peripheral, shadow_base, **kwargs):
    """ Silences access to a memory region.

    Args:
        peripheral (dict): peripheral description
        shadow_base (int or None): unused, just for compatibility with other
                                   functions
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

def generate_peripheral(peripheral, shadow_base, **kwargs):
    """ Generates definition of a peripheral.

    Args:
        peripheral (dict): peripheral description
        shadow_base (int or None): shadow base address
        kwargs (dict): additional parameterss, including
                       'model' and 'properties'

    Returns:
        string: repl definition of the peripheral
    """

    result = '\n{}: {} @ {}\n'.format(
        peripheral['name'],
        kwargs['model'],
        generate_sysbus_registration(int(peripheral['address'], 0),
                                     shadow_base))

    for constant, val in peripheral['constants'].items():
        if constant == 'interrupt':
            result += '    -> cpu@{}\n'.format(val)
        else:
            result += '    {}: {}\n'.format(constant, val)

    if 'properties' in kwargs:
        for prop, val in kwargs['properties'].items():
            result += '    {}: {}\n'.format(prop, val())

    return result

def generate_spiflash(peripheral, shadow_base, **kwargs):
    """ Generates definition of an SPI controller with attached flash memory.

    Args:
        peripheral (dict): peripheral description
        shadow_base (int or None): shadow base address
        kwargs (dict): additional parameterss, including
                       'model' and 'properties'

    Returns:
        string: repl definition of the peripheral
    """

    flash_size = 0x2000000

    result = """
spi: SPI.LiteX_SPI @ {{
    {};
    {}
}}
""".format(
        generate_sysbus_registration(int(peripheral['address'], 0),
                                     shadow_base, skip_braces=True),
        generate_sysbus_registration(0xa0000000, shadow_base, size=flash_size,
                                     skip_braces=True, region='xip'))

    result += """
flash: SPI.Micron_MT25Q @ spi
    size: {}
""".format(flash_size)

    return result

def generate_repl():
    """ Generates platform definition.

    Returns:
        string: platform defition containing all supported
                peripherals and memory regions
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
                'frequency':
                    lambda: constants['system_clock_frequency']['value']
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
        },
        'spiflash': {
            'handler': generate_spiflash
        }
    }

    shadow_base = (constants['shadow_base']['value']
                   if 'shadow_base' in constants
                   else None)

    for mem_region in mem_regions.values():
        if mem_region['name'] not in non_generated_mem_regions:
            result += generate_memory_region(mem_region, shadow_base)

    result += generate_cpu()

    for name, peripheral in peripherals.items():
        if name not in name_to_handler:
            print('Skipping unsupported peripheral {} at {}'
                  .format(name, peripheral['address']))
            continue

        h = name_to_handler[name]
        result += h['handler'](peripheral, shadow_base, **h)

    return result

def parse_csv(data):
    """ Parses LiteX CSV file.

    Args:
        data (list): list of CSV file lines
    """

    # scan for CSRs first, so it's easier to resolve CSR-related constants
    # in the second pass
    for _type, _name, _address, _, __ in data:
        if _type == 'csr_base':
            peripherals[_name] = {'name': _name,
                                  'address': _address,
                                  'constants': {}}

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
                    local_name = _name[len(_csr_name)+1:]
                    peripherals[_csr_name]['constants'][local_name] = _val
                    found = True
                    break
            if not found:
                # if it's not a CSR-related constant, it must be a global one
                constants[_name] = {'name': _name, 'value': _val}
        elif _type == 'memory_region':
            mem_regions[_name] = {'name': _name,
                                  'address': _val,
                                  'size': _val2}
        else:
            print('Skipping unexpected CSV entry: {} {}'.format(_type, _name))

def calculate_offset(address, base, shadow_base=0):
    """ Calculates an offset between two addresses, taking optional
        shadow base into consideration.

    Args:
        address (int): first address
        base (int): second address
        shadow_base (int): mask of shadow address that is applied to `base`

    Returns:
        The minimal non-negative offset between `address` and `base`
        calculated with and without applying the `shadow_base`.
    """

    return min(a - base for a in (address, (address | shadow_base), (address & ~shadow_base)) if a >= base)

def generate_resc(repl_file, host_tap_interface=None, bios_binary=None, firmware_binary=None):
    """ Generates platform definition.

    Args:
        repl_file (string): path to Renode platform definition file
        host_tap_interface (string): name of the tap interface on host machine
                                     or None if no network should be configured
        bios_binary (string): path to the binary file of LiteX BIOS or None
                              if it should not be loaded into ROM
        firmware_binary (string): path to the firmware binary file or None
                                  if it should not be loaded into flash

    Returns:
        string: platform defition containing all supported peripherals
                and memory regions
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
    elif firmware_binary and 'flash_boot_address' in constants:
        # load firmware binary to spiflash to boot from there

        firmware_data = open(firmware_binary, 'rb').read()
        crc32 = zlib.crc32(firmware_data)

        flash_boot_address = int(constants['flash_boot_address']['value'], 0)
        flash_base = int(mem_regions['spiflash']['address'], 0)
        shadow_base = (int(constants['shadow_base']['value'], 0)
                       if 'shadow_base' in constants
                       else 0)
        firmware_image_offset = calculate_offset(flash_boot_address, flash_base, shadow_base)

        # this is a new file with padding, length & CRC prepended
        firmware_binary_crc = firmware_binary + '.with_crc'
        with open(firmware_binary_crc, 'wb') as with_crc:
            # pad the file with 0's at the beginning - the
            # firmware image might not be located at the
            # beginning of the flash
            with_crc.write((0).to_bytes(firmware_image_offset, byteorder='little'))
            # 4 bytes: the length of the image
            with_crc.write(len(firmware_data).to_bytes(4, byteorder='little'))
            # 4 bytes: the CRC of the image
            with_crc.write(crc32.to_bytes(4, byteorder='little'))
            # the image itself
            with_crc.write(firmware_data)

        result += 'spi.flash UseDataFromFile @{}\n'.format(firmware_binary_crc)

    result += 'start'
    return result

def print_or_save(filepath, lines):
    """ Prints given string on standard output or to the file.

    Args:
        filepath (string): path to the file lines should be written to
                           or '-' to write to a standard output
        lines (string): content to be printed/written
    """
    if filepath == '-':
        print(lines)
    else:
        with open(filepath, 'w') as f:
            f.write(lines)

def remove_comments(data):
    for line in data:
        if not line.lstrip().startswith('#'):
            yield line

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('conf_file',
                        help='CSV configuration generated by LiteX')
    parser.add_argument('--resc', action='store',
                        help='Output script file')
    parser.add_argument('--repl', action='store',
                        help='Output platform definition file')
    parser.add_argument('--configure-network', action='store',
                        help='Generate virtual network and connect it to host')
    parser.add_argument('--bios-binary', action='store',
                        help='Path to the BIOS binary')
    parser.add_argument('--firmware-binary', action='store',
                        help='Path to the binary to load into boot flash')
    args = parser.parse_args()

    with open(args.conf_file) as csvfile:
        parse_csv(list(csv.reader(remove_comments(csvfile))))

    if args.repl:
        print_or_save(args.repl, generate_repl())

    if args.resc:
        if not args.repl:
            print("REPL is needed when generating RESC file")
            sys.exit(1)
        else:
            print_or_save(args.resc, generate_resc(args.repl,
                                                   args.configure_network,
                                                   args.bios_binary,
                                                   args.firmware_binary))
