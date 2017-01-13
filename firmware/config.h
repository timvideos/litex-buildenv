/*
 * Copyright 2015 / TimVideo.us
 * Copyright 2015 / EnjoyDigital
 * Copyright 2017 Joel Addison <joel@addison.net.au>
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

#ifndef __CONFIG_H
#define __CONFIG_H

#include "processor.h"

enum {
	CONFIG_KEY_RES_PRIMARY = 0,
	CONFIG_KEY_RES_SECONDARY,
	CONFIG_KEY_BLEND_USER1,
	CONFIG_KEY_BLEND_USER2,
	CONFIG_KEY_BLEND_USER3,
	CONFIG_KEY_BLEND_USER4,

	CONFIG_KEY_COUNT
};

#define CONFIG_DEFAULTS { PROCESSOR_MODE_720p_60, PROCESSOR_MODE_720p_50, 1, 2, 3, 4 }

void config_init(void);
void config_write_all(void);
unsigned char config_get(unsigned char key);
void config_set(unsigned char key, unsigned char value);

#endif /* __CONFIG_H */
