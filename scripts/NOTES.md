

# Setting up the environment

### Step 1 - If your board requires a proprietary toolchain, install that.

  * Spartan 6 based boards require [Xilinx ISE](). 
    Xilinx ISE is a propitary toolchain which *must be installed manually*.

    This is *most* boards, including
     - MimasV2,
     - Opsis, 
     - Atlys,
     - Pipistrello,
     - TODO: minispartan6/minispartan6+

  * "Series 7" based boards require [Xilinx Vivado]().
    Xilinx Vivado is a propitary toolchain which *must be installed manually*.

    These boards include;
     - NeTV2,
     - Nexys_Video,
     - TODO: Arty

  * TODO: Cyclone V based boards require [Altera Quatras]()
    Altera Quatras is a propitary toolchain which *must be installed manually*.

    These boards include;
     - De Nano???

  * TODO: ICE40 based boards require [Yosys, Anancr-PNR]().
    [XXXX] is an open source toolchain which can be installed automatically.

    These boards include;
     - IceStick?
     - ???

### Step 2 - Install required system packages

 * `download-env-root.sh` does this.

 Bunch of packages are needed;
  * Libraries for talking to USB - libftdi, libusb, fxload
  
  * udev rules.

  * Kernel modules for some boards. Mostly not needed....

### Step 3 - Setup a self contained environment.

 * `download-env.sh` does this.

 The steps are;
  - Get conda
    Conda is a self contained Python install, kind of like virtualenv but
    includes the ability to install precompiled binary packages.

  - Install precompiled C compiler toolchain from TimVideos Conda repo. This
    includes; binutils, gcc and gdb.

     - The C compiler toolchain is needed for compiling the BIOS and firmware.

  - Install precompiled JTAG tool from from TimVideos Conda repo. The tool we
    use is openocd.

  - Install dependent Python packages (from pip/conda/elsewhere). Things like
    pyserial and stuff.

  - Install tools for simulation and testing. Things like verilator.

  - Install tools for helping manage FPGA boards. Things like
    HDMI2USB-mode-switch, MimasV2Config.py, flterm.

  - Initialising submodules and install litex packages from `third_party/`.

 This is completely contained in the `build/conda` directory. Removing that
 directory will totally remove the installed environment.

### Step 4 - Enter self contained environment & set environment variables.

 * `source scripts/enter-env.sh` - enter-env checks that your environment is
   setup correctly and contains all the dependencies you need.

 * `export PLATFORM=<platform>` - Default is Opsis
 * `export TARGET=<targetname>` - Default is dependent on the platform.

# After entering environment

### Build `gateware` for the FPGA

 * `make gateware`

### Load or Flash `gateware` onto the FPGA

 * This step is board specific.

#### `Flashing` verses `Loading`

 * `Loading` means to temporarily put something (gateware, firmware, etc) onto
   a device. After a power cycle, the device will return to the flashed
   configuration.

 * `Flashing` means to permanently  put something (gateware, firmware, etc)
   onto a device. After a power cycle, the device will reload the flashed
   configuration.

##### Random Comments

 * FPGAs loose their "configuration" when they loose power or are reset. When
   powered on they will load their configuration from a flash chip (normally
   SPI flash) on the FPGA board. 
   
 * Flashing is the process of writing a new configuration to the flash chip.

 * Flashing is generally slower than loading because it requires you to erase
   the contents of the flash, write the new contents and then verify the
   result.

 * Flashing is sometimes done by loading a "flash proxy" gateware onto the
   FPGA, which then allows the computer to communicate with the flash chip.

 * Some devices only support flashing and not loading (IE MimasV2)

