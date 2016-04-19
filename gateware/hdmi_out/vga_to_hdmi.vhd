----------------------------------------------------------------------------------
-- Company:
-- Engineer:
--
-- Create Date: 17.06.2015 21:34:43
-- Design Name:
-- Module Name: vga_to_hdmi - Behavioral
-- Project Name:
-- Target Devices:
-- Tool Versions:
-- Description:
--
-- Dependencies:
--
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
--
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library UNISIM;
use UNISIM.VComponents.all;

entity vga_to_hdmi is
    port ( pixel_clk : in std_logic;
           pixel_clk_x5 : in std_logic;
           reset  : in std_logic;

           c0_tmds_symbol : in std_logic_vector(9 downto 0);
           c1_tmds_symbol : in std_logic_vector(9 downto 0);
           c2_tmds_symbol : in std_logic_vector(9 downto 0);

           hdmi_tx_rscl  : out   std_logic;
           hdmi_tx_rsda  : inout std_logic;
           hdmi_tx_hpd   : in    std_logic;
           hdmi_tx_cec   : inout std_logic;
           hdmi_tx_clk_p : out   std_logic;
           hdmi_tx_clk_n : out   std_logic;
           hdmi_tx_p     : out   std_logic_vector(2 downto 0);
           hdmi_tx_n     : out   std_logic_vector(2 downto 0)
       );
end vga_to_hdmi;

architecture Behavioral of vga_to_hdmi is
    component serialiser_10_to_1 is
        Port ( clk : in STD_LOGIC;
               clk_x5 : in STD_LOGIC;
               reset  : in std_logic;
               data : in STD_LOGIC_VECTOR (9 downto 0);
               serial : out STD_LOGIC);
    end component;

    signal serial_clk : std_logic;
    signal serial_ch0 : std_logic;
    signal serial_ch1 : std_logic;
    signal serial_ch2 : std_logic;

    signal pixel_clk_buffered : std_logic;
begin
    hdmi_tx_rsda  <= 'Z';
    hdmi_tx_cec   <= 'Z';
    hdmi_tx_rscl  <= '1';

ser_ch0: serialiser_10_to_1 Port map (
        clk    => pixel_clk,
        clk_x5 => pixel_clk_x5,
        reset  => reset,
        data   => c0_tmds_symbol,
        serial => serial_ch0);

ser_ch1: serialiser_10_to_1 port map (
        clk    => pixel_clk,
        clk_x5 => pixel_clk_x5,
        reset  => reset,
        data   => c1_tmds_symbol,
        serial => serial_ch1);

ser_ch2: serialiser_10_to_1 port map (
        clk    => pixel_clk,
        clk_x5 => pixel_clk_x5,
        reset  => reset,
        data   => c2_tmds_symbol,
        serial => serial_ch2);

ser_clk: serialiser_10_to_1 Port map (
        clk    => pixel_clk,
        clk_x5 => pixel_clk_x5,
        reset  => reset,
        data   => "0000011111",
        serial => serial_clk);

clk_buf: OBUFDS generic map ( IOSTANDARD => "TMDS_33",  SLEW => "FAST")
    port map ( O  => hdmi_tx_clk_p, OB => hdmi_tx_clk_n, I => serial_clk);

tx0_buf: OBUFDS generic map ( IOSTANDARD => "TMDS_33",  SLEW => "FAST")
    port map ( O  => hdmi_tx_p(0), OB => hdmi_tx_n(0), I  => serial_ch0);

tx1_buf: OBUFDS generic map ( IOSTANDARD => "TMDS_33",  SLEW => "FAST")
    port map ( O  => hdmi_tx_p(1), OB => hdmi_tx_n(1), I  => serial_ch1);

tx2_buf: OBUFDS generic map ( IOSTANDARD => "TMDS_33",  SLEW => "FAST")
    port map ( O  => hdmi_tx_p(2), OB => hdmi_tx_n(2), I  => serial_ch2);

end Behavioral;
