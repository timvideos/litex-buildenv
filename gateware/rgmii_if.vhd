--------------------------------------------------------------------------------
-- File       : rgmii_v2_0_if.vhd
-- Author     : Xilinx Inc.
-- ------------------------------------------------------------------------------
-- (c) Copyright 2004-2009 Xilinx, Inc. All rights reserved.
--
-- This file contains confidential and proprietary information
-- of Xilinx, Inc. and is protected under U.S. and
-- international copyright and other intellectual property
-- laws.
--
-- DISCLAIMER
-- This disclaimer is not a license and does not grant any
-- rights to the materials distributed herewith. Except as
-- otherwise provided in a valid license issued to you by
-- Xilinx, and to the maximum extent permitted by applicable
-- law: (1) THESE MATERIALS ARE MADE AVAILABLE "AS IS" AND
-- WITH ALL FAULTS, AND XILINX HEREBY DISCLAIMS ALL WARRANTIES
-- AND CONDITIONS, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING
-- BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, NON-
-- INFRINGEMENT, OR FITNESS FOR ANY PARTICULAR PURPOSE; and
-- (2) Xilinx shall not be liable (whether in contract or tort,
-- including negligence, or under any other theory of
-- liability) for any loss or damage of any kind or nature
-- related to, arising under or in connection with these
-- materials, including for any direct, or any indirect,
-- special, incidental, or consequential loss or damage
-- (including loss of data, profits, goodwill, or any type of
-- loss or damage suffered as a result of any action brought
-- by a third party) even if such damage or loss was
-- reasonably foreseeable or Xilinx had been advised of the
-- possibility of the same.
--
-- CRITICAL APPLICATIONS
-- Xilinx products are not designed or intended to be fail-
-- safe, or for use in any application requiring fail-safe
-- performance, such as life-support or safety devices or
-- systems, Class III medical devices, nuclear facilities,
-- applications related to the deployment of airbags, or any
-- other applications that could lead to death, personal
-- injury, or severe property or environmental damage
-- (individually and collectively, "Critical
-- Applications"). Customer assumes the sole risk and
-- liability of any use of Xilinx products in Critical
-- Applications, subject only to applicable laws and
-- regulations governing limitations on product liability.
--
-- THIS COPYRIGHT NOTICE AND DISCLAIMER MUST BE RETAINED AS
-- PART OF THIS FILE AT ALL TIMES.
-- ------------------------------------------------------------------------------
-- Description:  This module creates a version 2.0 Reduced Gigabit Media
--               Independent Interface (RGMII v2.0) by instantiating
--               Input/Output buffers and Input/Output double data rate
--               (DDR) flip-flops as required.
--
--               This interface is used to connect the Ethernet MAC to
--               an external Ethernet PHY.
--               This module routes the rgmii_rxc from the phy chip
--               (via a bufg) onto the rx_clk line.
--               An IODELAY component is used to shift the input clock
--               to ensure that the set-up and hold times are observed.
--------------------------------------------------------------------------------

library unisim;
use unisim.vcomponents.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

--------------------------------------------------------------------------------
-- The entity declaration for the PHY IF design.
--------------------------------------------------------------------------------
entity rgmii_if is
    port(
      -- Synchronous resets
      tx_reset                      : in  std_logic;
      rx_reset                      : in  std_logic;

      -- The following ports are the RGMII physical interface: these will be at
      -- pins on the FPGA
      rgmii_txd                     : out std_logic_vector(3 downto 0);
      rgmii_tx_ctl                  : out std_logic;
      rgmii_txc                     : out std_logic;
      rgmii_rxd                     : in  std_logic_vector(3 downto 0);
      rgmii_rx_ctl                  : in  std_logic;
      rgmii_rxc                     : in  std_logic;

      -- The following signals are in the RGMII in-band status signals
      link_status                   : out std_logic;
      clock_speed                   : out std_logic_vector(1 downto 0);
      duplex_status                 : out std_logic;

      -- The following ports are the internal GMII connections from IOB logic
      -- to the TEMAC core
      txd_from_mac                  : in  std_logic_vector(7 downto 0);
      tx_en_from_mac                : in  std_logic;
      tx_er_from_mac                : in  std_logic;
      tx_clk                        : in  std_logic;
      crs_to_mac                    : out std_logic;
      col_to_mac                    : out std_logic;
      rxd_to_mac                    : out std_logic_vector(7 downto 0);
      rx_dv_to_mac                  : out std_logic;
      rx_er_to_mac                  : out std_logic;

      -- Receiver clock for the MAC and Client Logic
      rx_clk                        : out std_logic
      );

end rgmii_if;


architecture PHY_IF of rgmii_if is


  ------------------------------------------------------------------------------
  -- internal signals
  ------------------------------------------------------------------------------
  signal not_tx_clk90         : std_logic;                        -- Inverted version of tx_clk90.
  signal not_tx_clk           : std_logic;                        -- Inverted version of tx_clk.
  signal gmii_txd_rising      : std_logic_vector(7 downto 0);     -- gmii_txd signal registered on the rising edge of tx_clk.
  signal gmii_tx_en_rising    : std_logic;                        -- gmii_tx_en signal registered on the rising edge of tx_clk.


  signal rgmii_tx_ctl_rising  : std_logic;                        -- RGMII control signal registered on the rising edge of tx_clk.
  signal gmii_txd_falling     : std_logic_vector(3 downto 0);     -- gmii_txd signal registered on the falling edge of tx_clk.
  signal rgmii_tx_ctl_falling : std_logic;                        -- RGMII control signal registered on the falling edge of tx_clk.
  signal rgmii_txc_odelay     : std_logic;                        -- RGMII receiver clock ODDR output.
  signal rgmii_tx_ctl_odelay  : std_logic;                        -- RGMII control signal ODDR output.
  signal rgmii_txd_odelay     : std_logic_vector(3 downto 0);     -- RGMII data ODDR output.
  signal rgmii_tx_ctl_int     : std_logic;                        -- Internal RGMII transmit control signal.

    signal rgmii_rxd_delay      : std_logic_vector(7 downto 0);
  signal rgmii_rx_ctl_delay   : std_logic;
  signal rx_clk_inv           : std_logic;

  signal rgmii_rx_ctl_reg     : std_logic;                        -- Internal RGMII receiver control signal.

  signal gmii_rxd_reg_int     : std_logic_vector(7 downto 0);     -- gmii_rxd registered in IOBs.
  signal gmii_rx_dv_reg_int   : std_logic;                        -- gmii_rx_dv registered in IOBs.
  signal gmii_rx_dv_reg       : std_logic;                        -- gmii_rx_dv registered in IOBs.
  signal gmii_rx_er_reg       : std_logic;                        -- gmii_rx_er registered in IOBs.
  signal gmii_rxd_reg         : std_logic_vector(7 downto 0);     -- gmii_rxd registered in IOBs.

  signal inband_ce            : std_logic;                        -- RGMII inband status registers clock enable

  signal rx_clk_int           : std_logic;


begin


   -----------------------------------------------------------------------------
   -- Route internal signals to output ports :
   -----------------------------------------------------------------------------

   rxd_to_mac      <= gmii_rxd_reg;
   rx_dv_to_mac    <= gmii_rx_dv_reg;
   rx_er_to_mac    <= gmii_rx_er_reg;


   -----------------------------------------------------------------------------
   -- RGMII Transmitter Clock Management :
   -----------------------------------------------------------------------------

   -- Delay the transmitter clock relative to the data.
   -- For 1 gig operation this delay is set to produce a 90 degree phase
   -- shifted clock w.r.t. gtx_clk_bufg so that the clock edges are
   -- centralised within the rgmii_txd[3:0] valid window.

   -- Invert the clock locally at the ODDR primitive
   not_tx_clk <= not(tx_clk);

   -- Instantiate the Output DDR primitive
   rgmii_txc_ddr : ODDR2
   generic map (
      DDR_ALIGNMENT  => "C0",
      SRTYPE         => "ASYNC"
   )
    port map (
       Q             => rgmii_txc_odelay,
       C0            => tx_clk,
       C1            => not_tx_clk,
       CE            => '1',
       D0            => '1',
       D1            => '0',
       R             => tx_reset,
       S             => '0'
   );


   -- Instantiate the Output Delay primitive (delay output by 2 ns)
   delay_rgmii_tx_clk : IODELAY2
   generic map (
      IDELAY_TYPE    => "FIXED",
      ODELAY_VALUE   => 30,     -- 50 ps per tap 0-255 taps
      DELAY_SRC      => "ODATAIN"
   )
   port map (
      BUSY           => open,
      DATAOUT        => open,
      DATAOUT2       => open,
      DOUT           => rgmii_txc,
      TOUT           => open,
      CAL            => '0',
      CE             => '0',
      CLK            => '0',
      IDATAIN        => '0',
      INC            => '0',
      IOCLK0         => '0',
      IOCLK1         => '0',
      ODATAIN        => rgmii_txc_odelay,
      RST            => '0',
      T              => '0'
   );



   -----------------------------------------------------------------------------
   -- RGMII Transmitter Logic :
   -- drive TX signals through IOBs onto RGMII interface
   -----------------------------------------------------------------------------

   -- Encode rgmii ctl signal
   rgmii_tx_ctl_int <= tx_en_from_mac xor tx_er_from_mac;


   -- Instantiate Double Data Rate Output components.
   -- Put data and control signals through ODELAY components to
   -- provide similiar net delays to those seen on the clk signal.

   gmii_txd_falling     <= txd_from_mac(7 downto 4);

   txdata_out_bus: for I in 3 downto 0 generate
   begin
      -- Instantiate the Output DDR primitive
      rgmii_txd_out : ODDR2
       generic map (
          DDR_ALIGNMENT => "C0",
          SRTYPE        => "ASYNC"
       )
       port map (
          Q             => rgmii_txd_odelay(I),
          C0            => tx_clk,
          C1            => not_tx_clk,
          CE            => '1',
          D0            => txd_from_mac(I),
          D1            => gmii_txd_falling(I),
          R             => tx_reset,
          S             => '0'
      );


      -- Instantiate the Output Delay primitive (delay output by 2 ns)
      delay_rgmii_txd : IODELAY2
      generic map (
         IDELAY_TYPE    => "FIXED",
         ODELAY_VALUE   => 0,     -- 50 ps per tap 0-255 taps
         DELAY_SRC      => "ODATAIN"
      )
      port map (
         BUSY           => open,
         DATAOUT        => open,
         DATAOUT2       => open,
         DOUT           => rgmii_txd(I),
         TOUT           => open,
         CAL            => '0',
         CE             => '0',
         CLK            => '0',
         IDATAIN        => '0',
         INC            => '0',
         IOCLK0         => '0',
         IOCLK1         => '0',
         ODATAIN        => rgmii_txd_odelay(I),
         RST            => '0',
         T              => '0'
      );
   end generate;

   -- Instantiate the Output DDR primitive
   rgmii_tx_ctl_out : ODDR2
    generic map (
       DDR_ALIGNMENT => "C0",
       SRTYPE        => "ASYNC"
    )
    port map (
       Q             => rgmii_tx_ctl_odelay,
       C0            => tx_clk,
       C1            => not_tx_clk,
       CE            => '1',
       D0            => tx_en_from_mac,
       D1            => rgmii_tx_ctl_int,
       R             => tx_reset,
       S             => '0'
   );


   -- Instantiate the Output Delay primitive (delay output by 2 ns)
   delay_rgmii_tx_ctl : IODELAY2
   generic map (
      IDELAY_TYPE    => "FIXED",
      ODELAY_VALUE   => 0,     -- 50 ps per tap 0-255 taps
      DELAY_SRC      => "ODATAIN"
   )
   port map (
      BUSY           => open,
      DATAOUT        => open,
      DATAOUT2       => open,
      DOUT           => rgmii_tx_ctl,
      TOUT           => open,
      CAL            => '0',
      CE             => '0',
      CLK            => '0',
      IDATAIN        => '0',
      INC            => '0',
      IOCLK0         => '0',
      IOCLK1         => '0',
      ODATAIN        => rgmii_tx_ctl_odelay,
      RST            => '0',
      T              => '0'
   );

   -----------------------------------------------------------------------------
   -- RGMII Receiver Clock Logic
   -----------------------------------------------------------------------------


   -----------------------------------------------------------------------------
   -- RGMII Receiver Clock Logic
   -----------------------------------------------------------------------------

   bufg_rgmii_rx_clk : BUFG
   port map (
      I                 => rgmii_rxc,
      O                 => rx_clk_int
   );


   -- Assign the internal clock signal to the output port
   rx_clk     <= rx_clk_int;
   rx_clk_inv <= not rx_clk_int;



   -----------------------------------------------------------------------------
   -- RGMII Receiver Logic : receive signals through IOBs from RGMII interface
   -----------------------------------------------------------------------------

   -- Instantiate Double Data Rate Input flip-flops.
   -- DDR_CLK_EDGE attribute specifies output data alignment from IDDR component

   rxdata_in_bus: for I in 3 downto 0 generate
      delay_rgmii_rxd : IODELAY2
      generic map (
         IDELAY_TYPE    => "FIXED",
         IDELAY_VALUE   => 40,
         DELAY_SRC      => "IDATAIN"
      )
      port map (
         BUSY           => open,
         DATAOUT        => rgmii_rxd_delay(I),
         DATAOUT2       => open,
         DOUT           => open,
         TOUT           => open,
         CAL            => '0',
         CE             => '0',
         CLK            => '0',
         IDATAIN        => rgmii_rxd(I),
         INC            => '0',
         IOCLK0         => '0',
         IOCLK1         => '0',
         ODATAIN        => '0',
         RST            => '0',
         T              => '1'
      );

      rgmii_rx_data_in : IDDR2
      generic map (
         DDR_ALIGNMENT  => "C0"
      )
      port map (
         Q0             => gmii_rxd_reg_int(I),
         Q1             => gmii_rxd_reg_int(I+4),
         C0             => rx_clk_int,
         C1             => rx_clk_inv,
         CE             => '1',
         D              => rgmii_rxd_delay(I),
         R              => '0',
         S              => '0'
      );

       -- pipeline the bottom 4 bits
       rxd_reg_pipe : process(rx_clk_int)
       begin
          if rx_clk_int'event and rx_clk_int ='1' then
             gmii_rxd_reg(I) <= gmii_rxd_reg_int(I);
          end if;
       end process rxd_reg_pipe;

       -- just pass the top 4 bits
       gmii_rxd_reg(I+4) <= gmii_rxd_reg_int(I+4);

   end generate;

   delay_rgmii_rx_ctl : IODELAY2
   generic map (
      IDELAY_TYPE    => "FIXED",
      IDELAY_VALUE   => 40,
      DELAY_SRC      => "IDATAIN"
   )
   port map (
      BUSY           => open,
      DATAOUT        => rgmii_rx_ctl_delay,
      DATAOUT2       => open,
      DOUT           => open,
      TOUT           => open,
      CAL            => '0',
      CE             => '0',
      CLK            => '0',
      IDATAIN        => rgmii_rx_ctl,
      INC            => '0',
      IOCLK0         => '0',
      IOCLK1         => '0',
      ODATAIN        => '0',
      RST            => '0',
      T              => '1'
   );

   rgmii_rx_ctl_in : IDDR2
   generic map (
      DDR_ALIGNMENT  => "C0"
   )
   port map (
      Q0             => gmii_rx_dv_reg_int,
      Q1             => rgmii_rx_ctl_reg,
      C0             => rx_clk_int,
      C1             => rx_clk_inv,
      CE             => '1',
      D              => rgmii_rx_ctl_delay,
      R              => '0',
      S              => '0'
   );

   rxdv_reg_pipe : process(rx_clk_int)
   begin
      if rx_clk_int'event and rx_clk_int ='1' then
         gmii_rx_dv_reg <= gmii_rx_dv_reg_int;
      end if;
   end process rxdv_reg_pipe;

   -- Decode gmii_rx_er signal
   gmii_rx_er_reg <= gmii_rx_dv_reg xor rgmii_rx_ctl_reg;


   -----------------------------------------------------------------------------
   -- RGMII Inband Status Registers :
   -- extract the inband status from received rgmii data
   -----------------------------------------------------------------------------

   -- Enable inband status registers during Interframe Gap
   inband_ce <= gmii_rx_dv_reg nor gmii_rx_er_reg;


   reg_inband_status : process(rx_clk_int)
   begin
      if rx_clk_int'event and rx_clk_int ='1' then
         if rx_reset = '1' then
            link_status                <= '0';
            clock_speed(1 downto 0)    <= "00";
            duplex_status              <= '0';
         elsif inband_ce = '1' then
            link_status             <= gmii_rxd_reg(0);
            clock_speed(1 downto 0) <= gmii_rxd_reg(2 downto 1);
            duplex_status           <= gmii_rxd_reg(3);
         end if;
      end if;
   end process reg_inband_status;


   -----------------------------------------------------------------------------
   -- Create the GMII-style Collision and Carrier Sense signals from RGMII
   -----------------------------------------------------------------------------

   col_to_mac <= (tx_en_from_mac or tx_er_from_mac) and (gmii_rx_dv_reg or gmii_rx_er_reg);
   crs_to_mac <= (tx_en_from_mac or tx_er_from_mac) or (gmii_rx_dv_reg or gmii_rx_er_reg);



end PHY_IF;
