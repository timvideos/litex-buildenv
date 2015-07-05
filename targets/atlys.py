# Support for the Digilent Atlys board - digilentinc.com/atlys/

from fractions import Fraction

from migen.fhdl.std import *
from migen.fhdl.specials import Keep
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.bus import wishbone

from misoclib.mem.sdram.module import SDRAMModule
from misoclib.mem.sdram.phy import s6ddrphy
from misoclib.mem.sdram.core.lasmicon import LASMIconSettings
from misoclib.mem.flash import spiflash
from misoclib.soc import mem_decoder
from misoclib.soc.sdram import SDRAMSoC
from misoclib.video import dvisampler
from misoclib.video import framebuffer

from misoclib.com.liteeth.common import *
from misoclib.com.liteeth.phy import LiteEthPHY
from misoclib.com.liteeth.phy.mii import LiteEthPHYMII
from misoclib.com.liteeth.core import LiteEthUDPIPCore
from misoclib.com.liteeth.frontend.etherbone import LiteEthEtherbone

from hdl.encoder import EncoderReader, Encoder, EncoderSender


class P3R1GE4JGF(SDRAMModule):
    # MIRA P3R1GE4JGF
    # Density: 1G bits
    # 8M words × 16 bits × 8 banks (P3R1GE4JGF) -- 1235E - G8E -- E20316JOR826
    # 2KB page size (P3R1GE4JGF) - Row address: A0 to A12 - Column address: A0 to A9
    # http://208.74.204.60/t5/Spartan-Family-FPGAs/Atlys-DDR2-memory/td-p/497304
    geom_settings = {
        "nbanks": 8,
        "nrows": 8192,
        "ncols": 1024
    }
    timing_settings = {
        "tRP":   12.5,
        "tRCD":  12.5,
        "tWR":   15,
        "tWTR":  3,
        "tREFI": 7800,
        "tRFC":  127.5, # 256Mb = 75ns, 512Mb = 105ns, 1Gb = 127.5ns, 2Gb = 197.5ns
    }

    def __init__(self, clk_freq):
        SDRAMModule.__init__(self, clk_freq, "DDR2", self.geom_settings,
            self.timing_settings)


class _CRG(Module):
    def __init__(self, platform, clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sdram_half = ClockDomain()
        self.clock_domains.cd_sdram_full_wr = ClockDomain()
        self.clock_domains.cd_sdram_full_rd = ClockDomain()
        self.clock_domains.cd_base50 = ClockDomain()

        self.clk4x_wr_strb = Signal()
        self.clk4x_rd_strb = Signal()

        f0 = 100*1000000
        clk100 = platform.request("clk100")
        clk100a = Signal()
        self.specials += Instance("IBUFG", i_I=clk100, o_O=clk100a)
        clk100b = Signal()
        self.specials += Instance("BUFIO2", p_DIVIDE=1,
                                  p_DIVIDE_BYPASS="TRUE", p_I_INVERT="FALSE",
                                  i_I=clk100a, o_DIVCLK=clk100b)
        f = Fraction(int(clk_freq), int(f0))
        n, m = f.denominator, f.numerator
        assert f0/n*m == clk_freq
        p = 8
        pll_lckd = Signal()
        pll_fb = Signal()
        pll = Signal(6)
        self.specials.pll = Instance("PLL_ADV", p_SIM_DEVICE="SPARTAN6",
                                     p_BANDWIDTH="OPTIMIZED", p_COMPENSATION="INTERNAL",
                                     p_REF_JITTER=.01, p_CLK_FEEDBACK="CLKFBOUT",
                                     i_DADDR=0, i_DCLK=0, i_DEN=0, i_DI=0, i_DWE=0, i_RST=0, i_REL=0,
                                     p_DIVCLK_DIVIDE=1, p_CLKFBOUT_MULT=m*p//n, p_CLKFBOUT_PHASE=0.,
                                     i_CLKIN1=clk100b, i_CLKIN2=0, i_CLKINSEL=1,
                                     p_CLKIN1_PERIOD=1e9/f0, p_CLKIN2_PERIOD=0.,
                                     i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb, o_LOCKED=pll_lckd,
                                     o_CLKOUT0=pll[0], p_CLKOUT0_DUTY_CYCLE=.5,
                                     o_CLKOUT1=pll[1], p_CLKOUT1_DUTY_CYCLE=.5,
                                     o_CLKOUT2=pll[2], p_CLKOUT2_DUTY_CYCLE=.5,
                                     o_CLKOUT3=pll[3], p_CLKOUT3_DUTY_CYCLE=.5,
                                     o_CLKOUT4=pll[4], p_CLKOUT4_DUTY_CYCLE=.5,
                                     o_CLKOUT5=pll[5], p_CLKOUT5_DUTY_CYCLE=.5,
                                     p_CLKOUT0_PHASE=0., p_CLKOUT0_DIVIDE=p//4,  # sdram wr rd
                                     p_CLKOUT1_PHASE=0., p_CLKOUT1_DIVIDE=p//4,
                                     p_CLKOUT2_PHASE=270., p_CLKOUT2_DIVIDE=p//2,  # sdram dqs adr ctrl
                                     p_CLKOUT3_PHASE=250., p_CLKOUT3_DIVIDE=p//2,  # off-chip ddr
                                     p_CLKOUT4_PHASE=0., p_CLKOUT4_DIVIDE=p//1,
                                     p_CLKOUT5_PHASE=0., p_CLKOUT5_DIVIDE=p//1,  # sys
        )
        self.specials += Instance("BUFG", i_I=pll[5], o_O=self.cd_sys.clk)
        reset = ~platform.request("cpu_reset")
        self.clock_domains.cd_por = ClockDomain()
        por = Signal(max=1 << 11, reset=(1 << 11) - 1)
        self.sync.por += If(por != 0, por.eq(por - 1))
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)
        self.specials += AsyncResetSynchronizer(self.cd_por, reset)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll_lckd | (por > 0))
        self.specials += Instance("BUFG", i_I=pll[2], o_O=self.cd_sdram_half.clk)
        self.specials += Instance("BUFPLL", p_DIVIDE=4,
                                  i_PLLIN=pll[0], i_GCLK=self.cd_sys.clk,
                                  i_LOCKED=pll_lckd, o_IOCLK=self.cd_sdram_full_wr.clk,
                                  o_SERDESSTROBE=self.clk4x_wr_strb)
        self.comb += [
            self.cd_sdram_full_rd.clk.eq(self.cd_sdram_full_wr.clk),
            self.clk4x_rd_strb.eq(self.clk4x_wr_strb),
        ]
        clk_sdram_half_shifted = Signal()
        self.specials += Instance("BUFG", i_I=pll[3], o_O=clk_sdram_half_shifted)

        output_clk = Signal()
        clk = platform.request("ddram_clock")
        self.specials += Instance("ODDR2", p_DDR_ALIGNMENT="NONE",
                                  p_INIT=0, p_SRTYPE="SYNC",
                                  i_D0=1, i_D1=0, i_S=0, i_R=0, i_CE=1,
                                  i_C0=clk_sdram_half_shifted, i_C1=~clk_sdram_half_shifted,
                                  o_Q=output_clk)
        self.specials += Instance("OBUFDS", i_I=output_clk, o_O=clk.p, o_OB=clk.n)


        dcm_base50_locked = Signal()
        self.specials += Instance("DCM_CLKGEN",
                                  p_CLKFXDV_DIVIDE=2, p_CLKFX_DIVIDE=4, p_CLKFX_MD_MAX=1.0, p_CLKFX_MULTIPLY=2,
                                  p_CLKIN_PERIOD=10.0, p_SPREAD_SPECTRUM="NONE", p_STARTUP_WAIT="FALSE",

                                  i_CLKIN=clk100a, o_CLKFX=self.cd_base50.clk,
                                  o_LOCKED=dcm_base50_locked,
                                  i_FREEZEDCM=0, i_RST=ResetSignal())
        self.specials += AsyncResetSynchronizer(self.cd_base50, self.cd_sys.rst | ~dcm_base50_locked)
        platform.add_period_constraint(self.cd_base50.clk, 20)


class BaseSoC(SDRAMSoC):
    default_platform = "atlys"

    csr_map = {
        "ddrphy":   16,
    }
    csr_map.update(SDRAMSoC.csr_map)

    mem_map = {
        "firmware_ram": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SDRAMSoC.mem_map)

    def __init__(self, platform, firmware_ram_size=0x8000, **kwargs):
        clk_freq = 75*1000000
        SDRAMSoC.__init__(self, platform, clk_freq,
                          integrated_rom_size=0x8000,
                          sdram_controller_settings=LASMIconSettings(l2_size=128),
                          **kwargs)

        self.submodules.crg = _CRG(platform, clk_freq)

        self.submodules.firmware_ram = wishbone.SRAM(firmware_ram_size)
        self.register_mem("firmware_ram", self.mem_map["firmware_ram"], self.firmware_ram.bus, firmware_ram_size)

        if not self.integrated_main_ram_size:
            self.submodules.ddrphy = s6ddrphy.S6DDRPHY(platform.request("ddram"),
                                                       P3R1GE4JGF(self.clk_freq),
                                                       rd_bitslip=0,
                                                       wr_bitslip=4,
                                                       dqs_ddr_alignment="C0")
            self.comb += [
                self.ddrphy.clk4x_wr_strb.eq(self.crg.clk4x_wr_strb),
                self.ddrphy.clk4x_rd_strb.eq(self.crg.clk4x_rd_strb),
            ]
            self.register_sdram_phy(self.ddrphy)

        self.specials += Keep(self.crg.cd_sys.clk)
        platform.add_platform_command("""
NET "{sys_clk}" TNM_NET = "GRPsys_clk";
""", sys_clk=self.crg.cd_sys.clk)


class MiniSoC(BaseSoC):
    csr_map = {
        "ethphy": 17,
        "ethmac": 18,
    }
    csr_map.update(BaseSoC.csr_map)

    interrupt_map = {
        "ethmac": 2,
    }
    interrupt_map.update(BaseSoC.interrupt_map)

    mem_map = {
        "ethmac": 0x30000000,  # (shadow @0xb0000000)
    }
    mem_map.update(BaseSoC.mem_map)

    def __init__(self, platform, **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        self.submodules.ethphy = LiteEthPHY(platform.request("eth_clocks"), platform.request("eth"), clk_freq=self.clk_freq)
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32, interface="wishbone")
        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac", self.mem_map["ethmac"]+self.shadow_base, 0x2000)

        self.specials += [
            Keep(self.ethphy.crg.cd_eth_rx.clk),
            Keep(self.ethphy.crg.cd_eth_tx.clk)
        ]
        platform.add_platform_command("""
NET "{eth_clocks_rx}" CLOCK_DEDICATED_ROUTE = FALSE;
NET "{eth_rx_clk}" TNM_NET = "GRPeth_rx_clk";
NET "{eth_tx_clk}" TNM_NET = "GRPeth_tx_clk";
TIMESPEC "TSise_sucks1" = FROM "GRPeth_tx_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks2" = FROM "GRPsys_clk" TO "GRPeth_tx_clk" TIG;
TIMESPEC "TSise_sucks3" = FROM "GRPeth_rx_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks4" = FROM "GRPsys_clk" TO "GRPeth_rx_clk" TIG;
""", eth_clocks_rx=platform.lookup_request("eth_clocks").rx,
     eth_rx_clk=self.ethphy.crg.cd_eth_rx.clk,
     eth_tx_clk=self.ethphy.crg.cd_eth_tx.clk)


class EtherboneSoC(BaseSoC):
    csr_map = {
        "ethphy": 17,
        "ethcore": 18,
    }
    csr_map.update(BaseSoC.csr_map)

    def __init__(self, platform,
        mac_address=0x10e2d5000000,
        ip_address="192.168.1.42",
        **kwargs):
        BaseSoC.__init__(self, platform, **kwargs)

        # Ethernet PHY and UDP/IP stack
        self.submodules.ethphy = LiteEthPHYMII(platform.request("eth_clocks"), platform.request("eth"))
        self.submodules.ethcore = LiteEthUDPIPCore(self.ethphy, mac_address, convert_ip(ip_address), self.clk_freq)

        # Etherbone bridge
        self.submodules.etherbone = LiteEthEtherbone(self.ethcore.udp, 20000)
        self.add_wb_master(self.etherbone.master.bus)

        self.specials += [
            Keep(self.ethphy.crg.cd_eth_rx.clk),
            Keep(self.ethphy.crg.cd_eth_tx.clk)
        ]
        platform.add_platform_command("""
NET "{eth_clocks_rx}" CLOCK_DEDICATED_ROUTE = FALSE;
NET "{eth_clocks_rx}" TNM_NET = "GRPeth_clocks_rx";
NET "{eth_rx_clk}" TNM_NET = "GRPeth_rx_clk";
NET "{eth_tx_clk}" TNM_NET = "GRPeth_tx_clk";
TIMESPEC "TSise_sucks1" = FROM "GRPeth_clocks_rx" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks2" = FROM "GRPsys_clk" TO "GRPeth_clocks_rx" TIG;
TIMESPEC "TSise_sucks3" = FROM "GRPeth_tx_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks4" = FROM "GRPsys_clk" TO "GRPeth_tx_clk" TIG;
TIMESPEC "TSise_sucks5" = FROM "GRPeth_rx_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks6" = FROM "GRPsys_clk" TO "GRPeth_rx_clk" TIG;
""", eth_clocks_rx=platform.lookup_request("eth_clocks").rx,
     eth_rx_clk=self.ethphy.crg.cd_eth_rx.clk,
     eth_tx_clk=self.ethphy.crg.cd_eth_tx.clk)


class FramebufferSoC(EtherboneSoC):
    csr_map = {
        "fb": 19,
    }
    csr_map.update(EtherboneSoC.csr_map)

    def __init__(self, platform, **kwargs):
        EtherboneSoC.__init__(self, platform, **kwargs)

        self.submodules.fb = framebuffer.Framebuffer(None, platform.request("dvi_out"),
                                                     self.sdram.crossbar.get_master())

        platform.add_platform_command("""PIN "dviout_pix_bufg.O" CLOCK_DEDICATED_ROUTE = FALSE;""")

        self.specials += [
            Keep(self.fb.driver.clocking.cd_pix.clk)
        ]
        platform.add_platform_command("""
NET "{pix_clk}" TNM_NET = "GRPpix_clk";
TIMESPEC "TSise_sucks7" = FROM "GRPpix_clk" TO "GRPsys_clk" TIG;
TIMESPEC "TSise_sucks8" = FROM "GRPsys_clk" TO "GRPpix_clk" TIG;
""", pix_clk=self.fb.driver.clocking.cd_pix.clk)


class VideomixerSoC(FramebufferSoC):
    csr_map = {
        "dvisampler":          20,
        "dvisampler_edid_mem": 21
    }
    csr_map.update(FramebufferSoC.csr_map)

    interrupt_map = {
        "dvisampler": 3,
    }
    interrupt_map.update(FramebufferSoC.interrupt_map)

    def __init__(self, platform, **kwargs):
        FramebufferSoC.__init__(self, platform, **kwargs)
        self.submodules.dvisampler = dvisampler.DVISampler(platform.request("dvi_in", 1),
                                                           self.sdram.crossbar.get_master())


class VideostreamerSoC(VideomixerSoC):
    csr_map = {
        "encoder_reader": 22
    }
    csr_map.update(VideomixerSoC.csr_map)
    mem_map = {
        "encoder": 0x30000000,  # (shadow @0xb0000000)
    }
    mem_map.update(VideomixerSoC.mem_map)

    def __init__(self, platform, **kwargs):
        VideomixerSoC.__init__(self, platform, **kwargs)

        self.submodules.encoder_reader = EncoderReader(self.sdram.crossbar.get_master())
        self.submodules.encoder = Encoder(platform)
        encoder_port = self.ethcore.udp.crossbar.get_port(8000, 8)
        self.submodules.encoder_sender = EncoderSender(convert_ip("192.168.1.15"), 8000, 256)

        self.comb += [
            platform.request("user_led", 0).eq(self.encoder_reader.source.stb),
            platform.request("user_led", 1).eq(self.encoder_reader.source.ack),
            Record.connect(self.encoder_reader.source, self.encoder.sink),
            Record.connect(self.encoder.source, self.encoder_sender.sink),
            Record.connect(self.encoder_sender.source, encoder_port.sink)
        ]
        self.add_wb_slave(mem_decoder(self.mem_map["encoder"]), self.encoder.bus)
        self.add_memory_region("encoder", self.mem_map["encoder"]+self.shadow_base, 0x2000)

default_subtarget = MiniSoC
