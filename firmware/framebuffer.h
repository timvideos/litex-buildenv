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

#include <assert.h>
#include <stdint.h>
#include "generated/mem.h"

/**
 * Frame buffers must be aligned to XXX boundary.
 *
 *  0x01000000 - Pattern Buffer - Frame Buffer n
 *
 * Each input then has 3 frame buffers spaced like this;
 *  // HDMI Input 0
 *  0x02000000 - HDMI Input 0 - Frame Buffer n
 *  0x02040000 - HDMI Input 0 - Frame Buffer n+1
 *  0x02080000 - HDMI Input 0 - Frame Buffer n+2
 *  // HDMI Input 1
 *  0x03000000 - HDMI Input 1 - Frame Buffer n
 *  0x03040000 - HDMI Input 1 - Frame Buffer n+1
 *  0x03080000 - HDMI Input 1 - Frame Buffer n+2
 *  ...
 *  // HDMI Input x
 *  0x0.000000 - HDMI Input x - Frame Buffer n
 *  0x0.040000 - HDMI Input x - Frame Buffer n+1
 *  0x0.080000 - HDMI Input x - Frame Buffer n+2
 *
 */
#define FRAMEBUFFER_OFFSET		0x01000000
#define FRAMEBUFFER_PATTERNS		1

#define FRAMEBUFFER_PIXELS_X		1920	// pixels
#define FRAMEBUFFER_PIXELS_Y		1080	// pixels
#define FRAMEBUFFER_PIXELS_BYTES	2	// bytes

#define FRAMEBUFFER_BASE(x)			((x+1)*FRAMEBUFFER_OFFSET)
#define FRAMEBUFFER_BASE_PATTERN		FRAMEBUFFER_BASE(0)
#define FRAMEBUFFER_BASE_HDMI_INPUT(x)		FRAMEBUFFER_BASE(x+FRAMEBUFFER_PATTERNS)

// Largest frame size at 16bpp (ish)
#define FRAMEBUFFER_SIZE		0x400000 // bytes
#if (FRAMEBUFFER_PIXELS_X*FRAMEBUFFER_PIXELS_Y*FRAMEBUFFER_PIXELS_BYTES) > FRAMEBUFFER_SIZE
#error "Number of pixels don't fit in frame buffer"
#endif

#define FRAMEBUFFER_COUNT 		4			// Must be a multiple of 2
#define FRAMEBUFFER_MASK 		(FRAMEBUFFER_COUNT - 1)

typedef unsigned int fb_ptrdiff_t;
// FIXME: typedef uint16_t framebuffer_t[FRAMEBUFFER_SIZE];

inline unsigned int *fb_ptrdiff_to_main_ram(fb_ptrdiff_t p) {
#ifdef MAIN_RAM_BASE
	return (unsigned int *)(MAIN_RAM_BASE + p);
#else
/*       FIXME!  Should be unreachable if we have no main ram! */
        assert(0);
        return (unsigned int *)(0);
#endif
}

#endif /* __FRAMEBUFFER_H */
