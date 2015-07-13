#ifndef CDC_H
#define CDC_H

#include <fx2types.h>

#define SET_LINE_CODING		(0x20)
#define GET_LINE_CODING		(0x21)
#define SET_CONTROL_STATE	(0x22)

BOOL handleCDCCommand(BYTE cmd);

#endif // CDC_H
