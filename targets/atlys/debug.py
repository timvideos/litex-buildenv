from litex.soc.cores import uart
from litescope import LiteScopeAnalyzer
from .base import BaseSoC

# Connection Overview:
#
#      FPGA:
#                                                   |--> LiteScope
#   --SERIAL--> UARTWishboneBridge <--WISHBONE-BUS--+--> Crossover UART
#   |                                               |--> CPU Debug Interface
#   |
#   |  Host:
#   |                                               |-> LiteScope
#   |      |--->  litex_server  <--TCP-(ETHERBONE)--+-> litex_crossover_uart -> terminal
#   |      |                                        |-> wishbone-tool
#   |      |                                        |-> any custom python client that writes/reads any address
#   ^-----or
#          |                                        |-> terminal
#          |-->   wishbone-tool <-------------------+-> gdb
#                                                   |-> client that writes/reads any address
#
# See also TBD
#
# Note: The CPU Debug Interface is only available
#       if your CPU_VARIANT includes "debug".
#
# Note: You can run multiple litex_server clients or
#       wishbone-tool clients at the same time.
#
# There are currently two ways to connect to your UARTWishboneBridge:
#   1. Litex Server:
#       Usage: litex_server --uart --uart-port /dev/ttyXXX
#       - Features:
#           - LiteScope: (TBD)
#           - Crossover UART:
#               - cd into build/[target]/test/
#               - start litex_crossover_uart
#               - connect to /dev/pts/XXX (e.g minicom -D /dev/pts/XXX)
#           - CPU Debug Interface: (not supported)
#           - Wishbone-tool: wishbone-tool --ethernet-host 127.0.0.1 --ethernet-tcp
#   2. Wishbone Tool (https://github.com/litex-hub/wishbone-utils)
#       - Features:
#           - LiteScope: (not supported)
#           - Crossover UART: 
#               wishbone-tool --serial /dev/ttyXXX -s terminal --csr-csv build/[target]/test/csr.csv
#           - CPU Debug Interface: 
#               - wishbone-tool --serial /dev/ttyXXX -s gdb --csr-csv build/[target]/test/csr.csv
#               - start gdb: gdb -ex 'target remote :3333'

class DebugSoC(BaseSoC):

    def __init__(self, platform, *args, **kwargs):
    
        # Use the crossover uart that is able to connect over the uart bridge
        kwargs['uart_name']="crossover"
        
        BaseSoC.__init__(self, platform, *args, **kwargs)
        
        #Add the uart bridge (you may adapt the baudrate e.g 500000, 921600)
        self.submodules.uartbone  = uart.UARTWishboneBridge(
                pads     = self.platform.request("serial"),
                clk_freq = self.sys_clk_freq,
                baudrate = 115200)
        self.bus.add_master(name="uartbone", master=self.uartbone.wishbone)

        #add LitexScope
        analyzer_signals = [
            self.ddrphy.dfi,
            self.cpu.ibus.cyc,
            self.cpu.ibus.stb
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals,
            depth        = 2048,
            clock_domain = "sys")
        self.add_csr("analyzer")
        
    # Generate the configuration file for the LiteScope client
    def do_exit(self, vns, filename="test/analyzer.csv"):
        self.analyzer.export_csv(vns, filename)

SoC = DebugSoC
