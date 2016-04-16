
# Using Github Issues

## Label Meanings

#### `type-XXXX` Labels

These label refers to the "type" of the issue.

 * `type-bug`         - This issue talks about something that currently doesn't work, but should.
 * `type-enhancement` - This issue talks about something that should be added but currently not implemented.
 * `type-pie-in-sky`  - This issue talks about something we'd like to have in the future but is still a long way off and not currently being focused on.
 * `type-question`    - This issue is just a question that needs to be answered and probably needs some type of research.
 * `type-new-project`     - This issue relates to starting a new project which is related to the HDMI2USB project (and probably reuses / interfaces with the project).
 * `type-kind-of-related` - This issue is only kind of related to the HDMI2USB project. It could be a tool that would be useful for the HDMI2USB or some other type of thing.

#### `level-XXX` Labels

These labels don't really fit into the other categories.

 * `level-hardware`       - This issue relates to the creation and production of a physical device. It probably needs PCB design and electrical knowledge and a soldering iron.
 * `level-firmware`       - This issue relates to the creation of firmware running on a device connected to a computer.
 * `level-software`       - This issue relates to the creation of software on a computer.
 * `level-infrastructure` - This issue related to infrastructure around the project like the build system, continuous integration, etc.

#### `firmware-XXXX` Labels

These label refers to issues which are related to the various firmware which exists in the system.

 * `firmware-fgpa`    - This issue relates to the "gateware" that is loaded onto the FPGA. This means it probably needs VHDL or Verilog experiance to fix.
 * `firmware-cypress` - This issue relates to the firmware loaded onto a Cypress FX2 device (such as found on the Digilent Atlys and HDMI2USB Numato boards). This is written in dialect of C.
 * `firmware-lm32`    - This issue relates to the firmware running on the LM32 softcore inside the (FPGA). This is written in C.

#### `hdmi2XXXX` Labels

These label refers to issues which are related to a **specific** board configuration.

 * `hdmi2***` - This issue relates to all HDMI capture devices.
 * `hdmi2usb` - This issue relates to capturing via the USB port.
 * `hdmi2eth` - This issue relates to capturing via the Ethernet port.

#### `board-XXXX` Labels

These label refers to issues which are related to a **specific** board configuration.

 * `board-***`   - This issue relates to all boards.
 * `board-atlys` - This issue relates to the Digilent Atlys board.
 * `board-opsis` - This issue relates to *both* the Numato Opsis board.

#### `expansion-XXXX` Labels

These labels refers to issues which are related so specific *expansion* board.

 * `expansion-vmodvga` - This issue relates to the VGA capture board initially started by @Jahanzeb and then finished by @rohit91
 * `expansion-vmodserial` - This issue relates to the generic serial expansion board created by @ayushXXXX

