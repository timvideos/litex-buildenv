#ifndef __OLED_H
#define __OLED_H

#define OLED_RESET 0x01
#define OLED_DC    0x02
#define OLED_VBAT  0x04
#define OLED_VDD   0x08

#define SSD1306_SETCONTRAST         0x81
#define SSD1306_DISPLAYALLON_RESUME 0xa4
#define SSD1306_DISPLAYALLON        0xa5
#define SSD1306_NORMALDISPLAY       0xa6
#define SSD1306_INVERTDISPLAY       0xa7
#define SSD1306_DISPLAYOFF          0xae
#define SSD1306_DISPLAYON           0xaf
#define SSD1306_SETDISPLAYOFFSET    0xd3
#define SSD1306_SETCOMPINS          0xda
#define SSD1306_SETVCOMDETECT       0xdb
#define SSD1306_SETDISPLAYCLOCKDIV  0xd5
#define SSD1306_SETPRECHARGE        0xd9
#define SSD1306_SETMULTIPLEX        0xa8
#define SSD1306_SETLOWCOLUMN        0x00
#define SSD1306_SETHIGHCOLUMN       0x10
#define SSD1306_SETSTARTLINE        0x40
#define SSD1306_MEMORYMODE          0x20
#define SSD1306_COLUMNADDR          0x21
#define SSD1306_PAGEADDR            0x22
#define SSD1306_COMSCANINC          0xc0
#define SSD1306_COMSCANDEC          0xc8
#define SSD1306_SEGREMAP            0xa0
#define SSD1306_CHARGEPUMP          0x8d
#define SSD1306_EXTERNALVCC         0x01
#define SSD1306_SWITCHCAPVCC        0x02

#define SSD1306_ACTIVATE_SCROLL                      0x2f
#define SSD1306_DEACTIVATE_SCROLL                    0x2e
#define SSD1306_SET_VERTICAL_SCROLL_AREA             0xa3
#define SSD1306_RIGHT_HORIZONTAL_SCROLL              0x26
#define SSD1306_LEFT_HORIZONTAL_SCROLL               0x27
#define SSD1306_VERTICAL_AND_RIGHT_HORIZONTAL_SCROLL 0x29
#define SSD1306_VERTICAL_AND_LEFT_HORIZONTAL_SCROLL  0x2a

void oled_spi_write(unsigned char value);
void oled_write_command(unsigned char value);
void oled_write_data(unsigned char value);
void oled_init(void);
void oled_refresh(void);

#endif /* __OLED_H */
