#ifdef __lm32__

#define NOP __asm__("nop")

#elif __or1k__

#define NOP __asm__("l.nop")

#else

#error "Unknown ARCH."

#endif
