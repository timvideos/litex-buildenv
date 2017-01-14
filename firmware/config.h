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
	// Input config
	CONFIG_KEY_INPUT0_ENABLED,
	CONFIG_KEY_INPUT1_ENABLED,
	// Output 0 config
	CONFIG_KEY_OUTPUT0_ENABLED,
	CONFIG_KEY_OUTPUT0_SOURCE,
	// Output 1 config
	CONFIG_KEY_OUTPUT1_ENABLED,
	CONFIG_KEY_OUTPUT1_SOURCE,
	// Encoder config
	CONFIG_KEY_ENCODER_ENABLED,
	CONFIG_KEY_ENCODER_SOURCE,
	CONFIG_KEY_ENCODER_QUALITY,
	CONFIG_KEY_ENCODER_FPS,
	CONFIG_KEY_FX2_RESET,
	// Networking - MAC Address
	CONFIG_KEY_NETWORK_MAC0,
	CONFIG_KEY_NETWORK_MAC1,
	CONFIG_KEY_NETWORK_MAC2,
	CONFIG_KEY_NETWORK_MAC3,
	CONFIG_KEY_NETWORK_MAC4,
	CONFIG_KEY_NETWORK_MAC5,
	// Networking - IP address
	CONFIG_KEY_NETWORK_IP0,
	CONFIG_KEY_NETWORK_IP1,
	CONFIG_KEY_NETWORK_IP2,
	CONFIG_KEY_NETWORK_IP3,
	// Networking - DHCP enabled?
	CONFIG_KEY_NETWORK_DHCP,

	CONFIG_KEY_COUNT
};

void config_init(void);
void config_write_all(void);
unsigned char config_get(unsigned char key);
void config_set(unsigned char key, unsigned char value);

#endif /* __CONFIG_H */
