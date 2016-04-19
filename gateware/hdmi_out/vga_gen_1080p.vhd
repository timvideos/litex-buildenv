-----------------------------------------------------------------------------
-- File : vga_gen_1080p.vhd
--
-- Author : Mike Field <hamster@snap.net.nz>
--
-- Date    : 30th June 2015
--
-- Generate the VGA 1080p timing signals.
-- 
-----------------------------------------------------------------------------
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity vga_gen_1080p is
    Port ( clk : in STD_LOGIC;
           blank : out STD_LOGIC := '0';
           hsync : out STD_LOGIC := '0';
           vsync : out STD_LOGIC := '0');
end vga_gen_1080p;

architecture Behavioral of vga_gen_1080p is
    signal x : unsigned(11 downto 0) := (others => '0');
    signal y : unsigned(11 downto 0) := (others => '0');
begin

clk_proc: process(clk)
    begin
        if rising_edge(clk) then
            if x = 1920 then
                blank <= '1';
            elsif x = 2200-1 and (y < 1080-1 or y = 1125-1) then
                blank <= '0';            
            end if;
            
            if x = 1920+88-1 then
                hsync <= '1';
            elsif x = 1920+88+44-1 then
                hsync <= '0';
            end if;

            if x = 2200-1 then 
                x <= (others => '0');
                
                if y = 1080+4-1 then
                    vsync  <= '1';
                elsif y = 720+4+5-1 then
                    vsync  <= '0';
                end if;
                
                if y = 1125-1 then
                    y <= (others => '0');
                else
                    y <= y +1;
                end if;
            else
                x <= x + 1;        
            end if;            
        end if;            
    end process;
end Behavioral;