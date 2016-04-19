-----------------------------------------------------------------------------
-- Project: Nexys Video 1080p - top level for testing
--
-- File : top_level.vhd
--
-- Author : Mike Field <hamster@snap.net.nz>
--
-- Date    : 30th June 2015
--
-----------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

Library UNISIM;
use UNISIM.vcomponents.all;

entity vga_gen is
    Port (
        pixel_clk : in std_logic;

        vga_hsync  : out std_logic;
        vga_vsync  : out std_logic;
        vga_red    : out std_logic_vector(7 downto 0);
        vga_green  : out std_logic_vector(7 downto 0);
        vga_blue   : out std_logic_vector(7 downto 0);
        vga_blank  : out std_logic
);
end vga_gen;

architecture Behavioral of vga_gen is
    signal blank : std_logic := '0';
    signal hsync : std_logic := '0';
    signal vsync : std_logic := '0';

    component vga_gen_1080p is
        port (
           clk        : in  std_logic;

           blank      : out std_logic;
           hsync      : out std_logic;
           vsync      : out std_logic
           );
    end component;

    component vga_output is
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
    end component;

    signal count         : std_logic_vector(7 downto 0);

begin

i_vga_gen_1080p: vga_gen_1080p port map (
        clk        => pixel_clk,
        blank      => blank,
        hsync      => hsync,
        vsync      => vsync
    );

count_process: process(pixel_clk)
    begin
        if rising_edge(pixel_clk) then
            if blank = '1' then
                count <= (others => '0');
            else
                count <= std_logic_vector(unsigned(count)+1);
            end if;
        end if;
    end process;

i_vga_output: vga_output Port map (
            clk       => pixel_clk,
            hsync_in  => hsync,
            vsync_in  => vsync,
            blank_in  => blank,
            count     => count,
            vga_hsync => vga_hsync,
            vga_vsync => vga_vsync,
            vga_red   => vga_red,
            vga_green => vga_green,
            vga_blue  => vga_blue,
            vga_blank => vga_blank
        );

end Behavioral;