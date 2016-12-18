#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <console.h>
#include <string.h>
#include <generated/csr.h>
#include <generated/mem.h>

#include "stdio_wrap.h"

#include "version.h"
#include "version_data.h"

#define ALIGNMENT 4

static void print_csr_string(unsigned int addr, size_t size);
static void print_csr_string(unsigned int addr, size_t size) {
	size_t i;
	void* ptr = (void*)addr;
	for (i = 0; i < (size * ALIGNMENT); i += ALIGNMENT) {
		unsigned char c = MMPTR(ptr+i);
		if (c == '\0')
			return;
		// FIXME: Wrap putchar
                putchar(c);
	}
}

static void print_csr_hex(unsigned int addr, size_t size);
static void print_csr_hex(unsigned int addr, size_t size) {
	size_t i = 0;
	void* ptr = (void*)addr;
	for (i = 0; i < (size * ALIGNMENT); i += ALIGNMENT) {
		unsigned char v = MMPTR(ptr+i);
		wprintf("%02x", v);
	}
}

void print_board_dna(void) {
#ifdef CSR_DNA_ID_ADDR
	print_csr_hex(CSR_DNA_ID_ADDR, CSR_DNA_ID_SIZE);
#else
	wprintf("Unknown");
#endif
}

void print_version(void) {
	wprintf("hardware version info\r\n");
	wprintf("===============================================\r\n");
	wprintf("           DNA: ");
	print_board_dna();
	wprintf("\r\n");
	wprintf("\r\n");
	wprintf("gateware version info\r\n");
	wprintf("===============================================\r\n");
#ifdef CSR_PLATFORM_INFO_PLATFORM_ADDR
	wprintf("      platform: ");
	print_csr_string(CSR_PLATFORM_INFO_PLATFORM_ADDR, CSR_PLATFORM_INFO_PLATFORM_SIZE);
	wprintf("\r\n");
#endif
#ifdef CSR_PLATFORM_INFO_TARGET_ADDR
	wprintf("        target: ");
	print_csr_string(CSR_PLATFORM_INFO_TARGET_ADDR, CSR_PLATFORM_INFO_TARGET_SIZE);
	wprintf("\r\n");
#endif
#ifdef CSR_GIT_INFO_COMMIT_ADDR
	wprintf("      revision: ");
	print_csr_hex(CSR_GIT_INFO_COMMIT_ADDR, CSR_GIT_INFO_COMMIT_SIZE);
	wprintf("\r\n");
#endif
//	wprintf("misoc revision: %08x\r\n", identifier_revision_read());
	wprintf("\r\n");
	wprintf("firmware version info\r\n");
	wprintf("===============================================\r\n");
	wprintf("      platform: %s\n", board);
	wprintf("        target: %s\n", target);
	wprintf("    git commit: %s\n", git_commit);
	wprintf("    git branch: %s\n", git_branch);
	wprintf("  git describe: %s\n", git_describe);
	wprintf("    git status:\n%s\n", git_status);
	wprintf("         built: "__DATE__" "__TIME__"\r\n");
	wprintf("-----------------------------------------------\r\n");
}
