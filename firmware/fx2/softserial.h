
#include "fx2types.h"

void sio0_init( WORD baud_rate ) __critical ; // baud_rate max should be 57600 since int=2 bytes

void putchar(char c);
char getchar();
