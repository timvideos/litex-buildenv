
#include <fx2regs.h>
#include <fx2macros.h>
#include <delay.h>

#include "cdc.h"

#define SYNCDELAY SYNCDELAY4

BYTE __xdata LineCode[7] = {0x60,0x09,0x00,0x00,0x00,0x00,0x08};

BOOL handleCDCCommand(BYTE cmd) {
    int i;

    switch(cmd) {
    case SET_LINE_CODING:
        
        EUSB = 0 ;
        SUDPTRCTL = 0x01;
        EP0BCL = 0x00;
        SUDPTRCTL = 0x00;
        EUSB = 1;
        
        while (EP0BCL != 7);
            SYNCDELAY;

        for (i=0;i<7;i++)
            LineCode[i] = EP0BUF[i];

        return TRUE;

    case GET_LINE_CODING:
        
        SUDPTRCTL = 0x01;
        
        for (i=0;i<7;i++)
            EP0BUF[i] = LineCode[i];

        EP0BCH = 0x00;
        SYNCDELAY;
        EP0BCL = 7;
        SYNCDELAY;
        while (EP0CS & 0x02);
        SUDPTRCTL = 0x00;
        
        return TRUE;

    case SET_CONTROL_STATE:
        return TRUE;

    default:
        return FALSE;
    }
}
