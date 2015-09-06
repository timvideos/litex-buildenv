#ifndef __PATTERN_H
#define __PATTERN_H

/* Colors in YCBCR422 format (see pattern.py) */
#define YCBCR422_WHITE  0x80ff80ff
#define YCBCR422_YELLOW 0x00e194e1
#define YCBCR422_CYAN   0xabb200b2
#define YCBCR422_GREEN  0x2b951595
#define YCBCR422_PURPLE 0xd469e969
#define YCBCR422_RED    0x544cff4c
#define YCBCR422_BLUE   0xff1d6f1d
#define YCBCR422_BLACK  0x80108010

unsigned int pattern_framebuffer_base(void);

void pattern_fill_framebuffer(int h_active, int m_active);
void pattern_service(void);

#endif /* __PATTERN_H */
