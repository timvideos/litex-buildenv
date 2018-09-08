#ifdef __lm32__

#define REBOOT __asm__("call r0")
#define NOP __asm__("nop")

#elif __or1k__

#define REBOOT __asm__("l.j 0")
#define NOP __asm__("l.nop")

#elif __picorv32__

#define REBOOT __asm__("jalr x0, 0")
#define NOP __asm__("nop")

#elif __vexriscv__

#define REBOOT __asm__("jalr x0, 0")
#define NOP __asm__("nop")

#else

#error "Unknown ARCH."

#endif
