#ifndef __ENCODER_H
#define __ENCODER_H

#define ENCODER_START_REG          0x0
#define ENCODER_IMAGE_SIZE_REG     0x4
#define ENCODER_RAM_ACCESS_REG     0x8
#define ENCODER_STS_REG            0xC
#define ENCODER_COD_DATA_ADDR_REG  0x10
#define ENCODER_LENGTH_REG         0x14

#define ENCODER_QUANTIZER_RAM_LUMA_BASE 0x100

const char luma_rom_100[64];
const char luma_rom_85[64];
const char luma_rom_75[64];
const char luma_rom_50[64];

#define ENCODER_QUANTIZER_RAM_CHROMA_BASE 0x200

const char chroma_rom_100[64];
const char chroma_rom_85[64];
const char chroma_rom_75[64];
const char chroma_rom_50[64];

char encoder_enabled;
int encoder_target_fps;
int encoder_fps;
int encoder_quality;

void encoder_write_reg(unsigned int adr, unsigned int value);
unsigned int encoder_read_reg(unsigned int adr);
void encoder_init(int encoder_quality);
void encoder_start(short resx, short resy);
int encoder_done(void);
void encoder_enable(char enable);
int encoder_set_quality(int quality);
int encoder_set_fps(int fps);
void encoder_service(void);

#endif