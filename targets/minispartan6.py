from migen.fhdl.std import *
from migen.bus import wishbone

from misoclib.soc import SoC

class _CRG(Module):
	def __init__(self, clk_in):
		self.clock_domains.cd_sys = ClockDomain()
		self.clock_domains.cd_por = ClockDomain(reset_less=True)

		# Power on Reset (vendor agnostic)
		rst_n = Signal()
		self.sync.por += rst_n.eq(1)
		self.comb += [
			self.cd_sys.clk.eq(clk_in),
			self.cd_por.clk.eq(clk_in),
			self.cd_sys.rst.eq(~rst_n)
		]

class BaseSoC(SoC):
	default_platform = "minispartan6"
	def __init__(self, platform, **kwargs):
		SoC.__init__(self, platform,
			clk_freq=50*1000000,
			with_rom=True,
			with_sdram=True, sdram_size=16*1024,
			**kwargs)
		self.submodules.crg = _CRG(platform.request("clk50"))

default_subtarget = BaseSoC
