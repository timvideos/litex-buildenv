#ifndef __I2C_H
#define __I2C_H

#define I2C_SCL 0x01
#define I2C_SDAOE	0x02
#define I2C_SDAOUT	0x04

#define I2C_SDAIN	0x01

int i2c_init(void);
void i2c_delay(void);
unsigned int i2c_read_bit(void);
void i2c_write_bit(unsigned int bit);
void i2c_start_cond(void);
void i2c_stop_cond(void);
unsigned int i2c_write(unsigned char byte);
unsigned char i2c_read(int ack);

#endif /* __I2C_H */
