from litex.soc.cores import uart
from litescope import LiteScopeAnalyzer
from .base import BaseSoC

# Connection Overview:
#
#                                  |---> LiteScope
# HOST <--> UARTWishboneBridge <---|---> Crossover UART
#                                  |---> CPU Debug Interface
#                                       
# Note: The CPU Debug Interface is only available 
#       if your CPU_VARIANT includes "debug"
#
# There are currently two ways to connect to your UARTWishboneBridge:
#   1. Litex Server:
#       Usage: litex_server --uart --uart-port /dev/ttyXXX
#       - Features:
#           - LiteScope: (todo)
#           - Crossover UART:
#               - cd into build/[target]/test/
#               - start litex_crossover_uart
#               - connect to /dev/pts/XXX (e.g minicom -D /dev/pts/XXX)
#           - CPU Debug Interface: (not supported)
#   2. Wishbone Tool (https://github.com/litex-hub/wishbone-utils)
#       - Features:
#           - LiteScope: (not supported)
#           - Crossover UART: 
#               wishbone-tool -s terminal --csr-csv build/[target]/test/csr.csv
#           - CPU Debug Interface: 
#               - wishbone-tool -s gdb --csr-csv build/[target]/test/csr.csv
#               - start gdb
#                   - issue: target remote :1234

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
