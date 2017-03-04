#ifndef __CONFIG_H
#define __CONFIG_H

enum {
	CONFIG_KEY_RESOLUTION = 0,
	CONFIG_KEY_BLEND_USER1,
	CONFIG_KEY_BLEND_USER2,
	CONFIG_KEY_BLEND_USER3,
	CONFIG_KEY_BLEND_USER4,

	CONFIG_KEY_COUNT
};

#ifdef BOARD_MINISPARTAN6
#define CONFIG_DEFAULTS { 5, 1, 2, 3, 4 }
#else
#define CONFIG_DEFAULTS { 9, 1, 2, 3, 4 }
#endif

void config_init(void);
void config_write_all(void);
unsigned char config_get(unsigned char key);
void config_set(unsigned char key, unsigned char value);

#endif /* __CONFIG_H */
