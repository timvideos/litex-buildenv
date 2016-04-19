-----------------------------------------------------------------------------
-- File : vga_output.vhd
--
-- Author : Mike Field <hamster@snap.net.nz>
--
-- Date    : 9th May 2015
--
-- Just put some colours in the VGA sync signals
--
----------------------------------------------------------------------------
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

Library UNISIM;
use UNISIM.vcomponents.all;

entity vga_output is
    Port ( clk : in STD_LOGIC;
           hsync_in : in STD_LOGIC;
           vsync_in : in STD_LOGIC;
           blank_in : in STD_LOGIC;
           count     : in STD_LOGIC_VECTOR(7 downto 0);
           vga_hsync : out std_logic;
           vga_vsync : out std_logic;
           vga_red   : out std_logic_vector(7 downto 0);
           vga_green : out std_logic_vector(7 downto 0);
           vga_blue  : out std_logic_vector(7 downto 0);
           vga_blank : out std_logic);
end vga_output;

architecture Behavioral of vga_output is
begin
vga_buffer: process(clk)
    begin
        if rising_edge(clk) then
            vga_hsync <= hsync_in;
            vga_vsync <= vsync_in;
            if blank_in = '0' then
                vga_green <= count( 5 downto 4) & count( 5 downto 4) & count( 5 downto 4) & count( 5 downto 4);
                vga_red   <= count( 3 downto 2) & count( 3 downto 2) & count( 3 downto 2) & count( 3 downto 2);
                vga_blue  <= count( 1 downto 0) & count( 1 downto 0) & count( 1 downto 0) & count( 1 downto 0);
                vga_blank <= '0';
            else
                vga_red    <= (others => '0');
                vga_green  <= (others => '0');
                vga_blue   <= (others => '0');   
                vga_blank <= '1';
            end if;
        end if;
    end process;

end Behavioral;
