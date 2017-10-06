/*
 * Copyright 2017 Stefano Rivera <stefano@rivera.za.net>
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 */

#ifndef __FRAMEBUFFER_H
#define __FRAMEBUFFER_H

#include <stdint.h>
#include "generated/mem.h"

// Largest frame size at 16bpp (ish)
#define FRAMEBUFFER_SIZE (1920*1080*2)
#define FRAMEBUFFER_COUNT 4
#define FRAMEBUFFER_MASK (FRAMEBUFFER_COUNT - 1)
typedef unsigned int fb_ptrdiff_t;
// FIXME: typedef uint16_t framebuffer_t[FRAMEBUFFER_SIZE];

inline unsigned int *fb_ptrdiff_to_main_ram(fb_ptrdiff_t p) {
	return (unsigned int *)(MAIN_RAM_BASE + p);
}

#endif /* __FRAMEBUFFER_H */
