#include <stdio.h>
#include <string.h>
#include <generated/mem.h>

#include "config.h"

static const unsigned char config_defaults[CONFIG_KEY_COUNT] = CONFIG_DEFAULTS;
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
