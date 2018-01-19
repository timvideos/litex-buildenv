INCLUDE generated/output_format.ld
ENTRY(_start)

__DYNAMIC = 0;

INCLUDE generated/regions.ld

/* XXX: Elbert v2 hack, without main RAM -- offset in spiflash

        platforms/elbertv2/base.py:
        self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size

        generated/regions.ld:
        spiflash : ORIGIN = 0x20000000, LENGTH = 0x00200000

        targets/elbertv2.py:
        gateware_size = 0x10000

        platforms/elbertv2/base.py:
        bios_size = 0x8000

        Plus there is some values at the start of the flash (length/CRC)
        which we need to skip; call that 0x100

        .data has to go into sram, because needs to be writable and there
        is no where else.
*/
MEMORY {
	main_base : ORIGIN = 0x20018100, LENGTH = 0x001e7f00
}
/* XXX: ^^^^^ Elbert v2 hack */

SECTIONS
{
	.text :
	{
		_ftext = .;
		*(.text .stub .text.* .gnu.linkonce.t.*)
		_etext = .;
	} > main_base

	.rodata :
	{
		. = ALIGN(4);
		_frodata = .;
		*(.rodata .rodata.* .gnu.linkonce.r.*)
		*(.rodata1)
		_erodata = .;
	} > main_base

	.data :
	{
		. = ALIGN(4);
		_fdata = .;
		*(.data .data.* .gnu.linkonce.d.*)
		*(.data1)
		_gp = ALIGN(16);
		*(.sdata .sdata.* .gnu.linkonce.s.*)
		_edata = .;
	} > sram

	.bss :
	{
		. = ALIGN(4);
		_fbss = .;
		*(.dynsbss)
		*(.sbss .sbss.* .gnu.linkonce.sb.*)
		*(.scommon)
		*(.dynbss)
		*(.bss .bss.* .gnu.linkonce.b.*)
		*(COMMON)
		. = ALIGN(4);
		_ebss = .;
		_end = .;
	} > sram
}

PROVIDE(_fstack = ORIGIN(sram) + LENGTH(sram) - 4);
