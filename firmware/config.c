#include <generated/csr.h>
#include <stdbool.h>
#include <string.h>

#ifndef LOCALIP1
//#warning "No default IP address"
#define LOCALIP1 0
#define LOCALIP2 0
#define LOCALIP3 0
#define LOCALIP4 0
#endif

#include "config.h"
#include "processor.h"

// Order of default;
//   HDMI_IN1 (if it exists)
//   HDMI_IN0 (if it exists)
//   PATTERN
#ifdef CSR_HDMI_IN1_BASE
	#define VIDEO_IN_DEFAULT VIDEO_IN_HDMI_IN1
//	#warning "Default HDMI In 1"
#else
#ifdef CSR_HDMI_IN0_BASE
	#define VIDEO_IN_DEFAULT VIDEO_IN_HDMI_IN0
//	#warning "Default HDMI In 0"
#else
	#define VIDEO_IN_DEFAULT VIDEO_IN_PATTERN
//	#warning "Default Pattern"
#endif
#endif


static const unsigned char config_defaults[CONFIG_KEY_COUNT] = {
#if PLATFORM_NETV2 || PLATFORM_NEXYS_VIDEO
	PROCESSOR_MODE_1920_1080_60,    // Primary
	EDID_SECONDARY_MODE_OFF,        // Secondary
#else
	// EDID Config
	PROCESSOR_MODE_720p_50, // Primary
	PROCESSOR_MODE_720p_60, // Secondary
#endif
	// Input config
	false, // Input0
	true,  // Input1
	// Output config
	true, VIDEO_IN_DEFAULT, // Output 0
	true, VIDEO_IN_PATTERN, // Output 1
	// Encoder
	true, VIDEO_IN_DEFAULT, 85, 25, true,
	// Networking - MAC Address
	0x10, 0xe2, 0xd5, 0x00, 0x00, 0x00,
	// Networking - IP Address
	LOCALIP1, LOCALIP2, LOCALIP3, LOCALIP4,
	// Networking - DHCP
	false,
};
static unsigned char config_values[CONFIG_KEY_COUNT];

void config_init(void)
{
	memcpy(config_values, config_defaults, CONFIG_KEY_COUNT);
}

void config_write_all(void)
{
}

unsigned char config_get(unsigned char key)
{
	return config_values[key];
}

void config_set(unsigned char key, unsigned char value)
{
}
