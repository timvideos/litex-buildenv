#ifndef __PATTERN_H
#define __PATTERN_H

unsigned int pattern_framebuffer_base(void);

void pattern_fill_framebuffer(int h_active, int m_active);
void pattern_service(void);

#endif /* __PATTERN_H */
