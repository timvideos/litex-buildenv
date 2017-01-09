/*
 * Copyright 2015 / TimVideo.us
 * Copyright 2015 / EnjoyDigital
 * Copyright 2016 Joel Stanley <joel@jms.id.au>
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

#include <stdio.h>
#include <stdlib.h>

#include "edid.h"

static struct video_timing mode = {
	// 720p @ 60Hz
	//1280  720     60 Hz   45 kHz          ModeLine "1280x720"             74.25  1280 1390 1430 165  0 720 725 730 750 +HSync +VSync 
		.pixel_clock = 7425,

		.h_active = 1280,
		.h_blanking = 370,
		.h_sync_offset = 220,
		.h_sync_width = 40,

		.v_active = 720,
		.v_blanking = 30,
		.v_sync_offset = 20,
		.v_sync_width = 5
	};

int main()
{
	int i;
	char *edid = malloc(128);

        generate_edid(edid, "OHW", "TV", 2015, "HDMI2USB-1", &mode);

	//generate_edid(&edid, "OHW", "TV", 2015, "HDMI2USB-2", &mode);

	for (i = 0; i < 128; i++) {
		printf("%02hhx", edid[i]);
	}
	printf("\n");

	free(edid);
};
