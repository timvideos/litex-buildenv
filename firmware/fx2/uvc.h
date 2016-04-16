#ifndef UVC_H
#define UVC_H

#include <fx2types.h>

//----------------------------------------------------------------------------
//	UVC definitions
//----------------------------------------------------------------------------
//#define UVC_SET_CUR                                     (0x01)
#define UVC_GET_CUR                                     (0x81)
#define UVC_GET_MIN                                     (0x82)
#define UVC_GET_MAX                                     (0x83)
//#define UVC_GET_RES                                     (0x84)
//#define UVC_GET_LEN                                     (0x85)
//#define UVC_GET_INFO                                    (0x86)
//#define UVC_GET_DEF                                     (0x87)



BOOL handleUVCCommand(BYTE cmd);

#endif // UVC_H
