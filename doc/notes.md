

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
  - Get conda.
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
 * If you installed Xilinx to anywhere other than `/opt/Xilinx/`, run
   `export XILINX_DIR=<path>`. This must be set before entering the
   environment, as it is not updated from within it.
 * `source scripts/enter-env.sh` - enter-env checks that your environment is
   setup correctly and contains all the dependencies you need.

 * `export PLATFORM=<platform>` - Default is Opsis
 * `export TARGET=<targetname>` - Default is dependent on the platform.

# After entering environment

### Build `gateware` for the FPGA

 * `make gateware`

### Load or Flash `gateware` onto the FPGA

 * This step is board specific.

<br>
<br>
<br>
<hr>
<br>
<br>
<br>

# Random Comments

## `Firmware` verses `Gateware`

 * `gateware` is for configuration of the FPGA. It is the "hardware
   description".

 * `firmware` is software which runs on a CPU (it can be either `SoftCPU` or
   `HardCPU`).

 * The `gateware` can include a `SoftCPU` which runs `firmware`.

 * Most HDMI2USB boards have two `firmware` blobs,
   - firmware which runs on the SoftCPU inside the gateware,
   - firmware which runs on the Cypress FX2 USB interface chip attached to the
     FPGA.

## `Migen`, `MiSoC`, `LiteX` & `LiteXXX`

 * `Migen` is the `Python HDL` which allows easy creation of gateware to run on
   an FPGA. It includes all the primitives needed to write things for the FPGA

 * `MiSoC` is a `SoC` (System on Chip) which uses `Migen`. It includes;
   - Multiple `SoftCPU` implementations,
   - a `CSR` (Config/Control Status Registers) bus
   - Bunch of peripherals

 * `LiteX` is @enjoy-digital 's *soft* fork of `Migen+MiSoC`.
   - LiteX combines both `Migen+MiSoC` into one repo.
   - LiteX includes legacy features removed from Migen+MiSoC which are still in
     use.
   - LiteX includes more experimental features that have not made it to
     Migen/MiSoC (and may never make it into Migen/MiSoC).
   - LiteX code should be *easily* portable to Migen/MiSoC if
     legacy/experimental features are not used and is done regularly.

 * LiteEth, LiteDRAM, liteSATA, litePCIe are all cores which provide
   functionality.

   - LiteEth is heavily used inside liteX


## `SoftCPU` verses `HardCPU`

 * A `SoftCPU` is a CPU which is defined by a HDL (like Verilog, VHDL or Migen)
   and is included in the gateware inside a FPGA. As the definition can be
   changed when creating the gateware, `SoftCPU`s are highly customisable.

 * A `HardCPU` is a CPU which is predefined piece of hardware. As it physical
   hardware it can't be changed.

 * Most manufactures sell chips which include a FPGA fabric and a `HardCPU` in
   one package.
    - These are often called `SoC` (System on Chip) FPGAs.
    - Generally the `HardCPU` is an ARM these days. (Although PowerPC was
      previously fairly common.)
    - Xilinx's range is called the `Zynq`.
    - Altera have the Cyclone V `SoC` series.

 * A `SoftCPU` runs `firmware`. 
    - Normally the first `firmware` is a small program like a "BIOS" which does
      initilisation (like setting up main ram, running memtest, etc) before
      loading a more useful firmware into "main ram" and jumping it.

    - The "BIOS" is normally embedded inside the gateware. However as this
      takes up resources that can't be reused, on smaller boards the BIOS is
      executed directly from external flash (normal SPI flash).

     - The "BIOS" in MiSoC/LiteX can load the primary firmware from;
       * FPGA ROM
       * Memory mapped SPI flash
       * Serial download (using flterm)
       * TFTP (via liteEth)

 * There are a bunch of common 32bit `SoftCPU` implementations;
   Proprietary `SoftCPU`s are;
     - Xilinx's MicroBlaze
     - Altera's Nios2

   FOSS `SoftCPU`s are;
     - LatticeMico32 - lm32
     - OpenRisc - mor1k
     - Clifford's Pico Risc-V
     - J-Core - sh4/sh2 implementation
     - ZPU - ???

  * MiSoC supports `lm32` and `mor1k`.
  * LiteX supports `lm32`, `mor1k` and has WIP support for `pico risc-v` and
    (maybe) soon `J-Core`.

## `Flashing` verses `Loading`

 * FPGAs (generally) loose their "configuration" when they loose power or are
   reset. When powered on they will load their configuration from a flash chip
   (normally SPI flash) on the FPGA board.

 * `Loading` means to temporarily put something (gateware, firmware, etc) onto
   a device. After a power cycle, the device will return to the flashed
   configuration.

 * `Flashing` means to permanently  put something (gateware, firmware, etc)
   onto a device. After a power cycle, the device will reload the flashed
   configuration.

 * Flashing is the process of writing a new configuration to the flash chip.

 * Flashing is generally slower than loading because it requires you to erase
   the contents of the flash, write the new contents and then verify the
   result.

 * Flashing is sometimes done by loading a "flash proxy" gateware onto the
   FPGA, which then allows the computer to communicate with the flash chip.

 * Some devices only support flashing and not loading (IE MimasV2)

