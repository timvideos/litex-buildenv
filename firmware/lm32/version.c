#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <console.h>
#include <string.h>
#include <generated/csr.h>
#include <generated/mem.h>

#include "version.h"
#include "version_data.h"

#define ALIGNMENT 4

static void print_csr_string(unsigned int addr, size_t size) {
	size_t i;
	void* ptr = (void*)addr;
	for (i = 0; i < (size * ALIGNMENT); i += ALIGNMENT) {
		unsigned char c = MMPTR(ptr+i);
		if (c == '\0')
			return;
                putchar(c);
	}
}

static void print_csr_hex(unsigned int addr, size_t size) {
	size_t i = 0;
	void* ptr = (void*)addr;
	for (i = 0; i < (size * ALIGNMENT); i += ALIGNMENT) {
		unsigned char v = MMPTR(ptr+i);
		printf("%02x", v);
	}
}

void print_board_dna(void) {
	print_csr_hex(CSR_DNA_ID_ADDR, CSR_DNA_ID_SIZE);
}

void print_version(void) {
	printf("hardware version info\r\n");
	printf("===============================================\r\n");
	printf("           DNA: ");
	print_board_dna();
	printf("\r\n");
	printf("\r\n");
	printf("gateware version info\r\n");
	printf("===============================================\r\n");
	printf("      platform: ");
	print_csr_string(CSR_PLATFORM_INFO_PLATFORM_ADDR, CSR_PLATFORM_INFO_PLATFORM_SIZE);
	printf("\r\n");
	printf("        target: ");
	print_csr_string(CSR_PLATFORM_INFO_TARGET_ADDR, CSR_PLATFORM_INFO_TARGET_SIZE);
	printf("\r\n");
	printf("      revision: ");
	print_csr_hex(CSR_GIT_INFO_COMMIT_ADDR, CSR_GIT_INFO_COMMIT_SIZE);
	printf("\r\n");
	printf("misoc revision: %08x\r\n", identifier_revision_read());
	printf("\r\n");
	printf("firmware version info\r\n");
	printf("===============================================\r\n");
	printf("    git commit: %s\n", git_commit);
	printf("    git branch: %s\n", git_branch);
	printf("  git describe: %s\n", git_describe);
	printf("    git status:\n%s\n", git_status);
	printf("         built: "__DATE__" "__TIME__"\r\n");
	printf("-----------------------------------------------\r\n");
}
