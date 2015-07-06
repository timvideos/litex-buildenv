-------------------------------------------------------------------------------
-- File Name :  AC_ROM.vhd
--
-- Project   : JPEG_ENC
--
-- Module    : AC_ROM
--
-- Content   : AC_ROM Luminance
--
-- Description :
--
-- Spec.     :
--
-- Author    : Michal Krepa
--
-------------------------------------------------------------------------------
-- History :
-- 20090228: (MK): Initial Creation.
-------------------------------------------------------------------------------
-- //////////////////////////////////////////////////////////////////////////////
-- /// Copyright (c) 2013, Jahanzeb Ahmad
-- /// All rights reserved.
-- ///
-- /// Redistribution and use in source and binary forms, with or without modification,
-- /// are permitted provided that the following conditions are met:
-- ///
-- ///  * Redistributions of source code must retain the above copyright notice,
-- ///    this list of conditions and the following disclaimer.
-- ///  * Redistributions in binary form must reproduce the above copyright notice,
-- ///    this list of conditions and the following disclaimer in the documentation and/or
-- ///    other materials provided with the distribution.
-- ///
-- ///    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
-- ///    EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
-- ///    OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
-- ///    SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
-- ///    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
-- ///    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
-- ///    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
-- ///    WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
-- ///    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
-- ///   POSSIBILITY OF SUCH DAMAGE.
-- ///
-- ///
-- ///  * http://opensource.org/licenses/MIT
-- ///  * http://copyfree.org/licenses/mit/license.txt
-- ///
-- //////////////////////////////////////////////////////////////////////////////
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
----------------------------------- LIBRARY/PACKAGE ---------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
-- generic packages/libraries:
-------------------------------------------------------------------------------
library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

-------------------------------------------------------------------------------
-- user packages/libraries:
-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
----------------------------------- ENTITY ------------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
entity AC_ROM is
  port
  (
        CLK                : in  std_logic;
        RST                : in  std_logic;
        runlength          : in  std_logic_vector(3 downto 0);
        VLI_size           : in  std_logic_vector(3 downto 0);

        VLC_AC_size        : out unsigned(4 downto 0);
        VLC_AC             : out unsigned(15 downto 0)
    );
end entity AC_ROM;

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
----------------------------------- ARCHITECTURE ------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
architecture RTL of AC_ROM is

  signal rom_addr : std_logic_vector(7 downto 0);

-------------------------------------------------------------------------------
-- Architecture: begin
-------------------------------------------------------------------------------
begin

  rom_addr <= runlength & VLI_size;

  -------------------------------------------------------------------
  -- AC-ROM
  -------------------------------------------------------------------
  p_AC_ROM : process(CLK)
  begin
    if CLK'event and CLK = '1' then
          case rom_addr is
            when X"00" =>
              VLC_AC_size <= to_unsigned(4, VLC_AC_size'length);
              VLC_AC      <= resize("1010", VLC_AC'length);
            when X"01" =>
              VLC_AC_size <= to_unsigned(2, VLC_AC_size'length);
              VLC_AC      <= resize("00", VLC_AC'length);
            when X"02" =>
              VLC_AC_size <= to_unsigned(2, VLC_AC_size'length);
              VLC_AC      <= resize("01", VLC_AC'length);
            when X"03" =>
              VLC_AC_size <= to_unsigned(3, VLC_AC_size'length);
              VLC_AC      <= resize("100", VLC_AC'length);
            when X"04" =>
              VLC_AC_size <= to_unsigned(4, VLC_AC_size'length);
              VLC_AC      <= resize("1011", VLC_AC'length);
            when X"05" =>
              VLC_AC_size <= to_unsigned(5, VLC_AC_size'length);
              VLC_AC      <= resize("11010", VLC_AC'length);
            when X"06" =>
              VLC_AC_size <= to_unsigned(7, VLC_AC_size'length);
              VLC_AC      <= resize("1111000", VLC_AC'length);
            when X"07" =>
              VLC_AC_size <= to_unsigned(8, VLC_AC_size'length);
              VLC_AC      <= resize("11111000", VLC_AC'length);
            when X"08" =>
              VLC_AC_size <= to_unsigned(10, VLC_AC_size'length);
              VLC_AC      <= resize("1111110110", VLC_AC'length);
            when X"09" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110000010", VLC_AC'length);
            when X"0A" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110000011", VLC_AC'length);
            when X"11" =>
              VLC_AC_size <= to_unsigned(4, VLC_AC_size'length);
              VLC_AC      <= resize("1100", VLC_AC'length);
            when X"12" =>
              VLC_AC_size <= to_unsigned(5, VLC_AC_size'length);
              VLC_AC      <= resize("11011", VLC_AC'length);
            when X"13" =>
              VLC_AC_size <= to_unsigned(7, VLC_AC_size'length);
              VLC_AC      <= resize("1111001", VLC_AC'length);
            when X"14" =>
              VLC_AC_size <= to_unsigned(9, VLC_AC_size'length);
              VLC_AC      <= resize("111110110", VLC_AC'length);
            when X"15" =>
              VLC_AC_size <= to_unsigned(11, VLC_AC_size'length);
              VLC_AC      <= resize("11111110110", VLC_AC'length);
            when X"16" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110000100", VLC_AC'length);
            when X"17" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110000101", VLC_AC'length);
            when X"18" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110000110", VLC_AC'length);
            when X"19" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110000111", VLC_AC'length);
            when X"1A" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110001000", VLC_AC'length);
            when X"21" =>
              VLC_AC_size <= to_unsigned(5, VLC_AC_size'length);
              VLC_AC      <= resize("11100", VLC_AC'length);
            when X"22" =>
              VLC_AC_size <= to_unsigned(8, VLC_AC_size'length);
              VLC_AC      <= resize("11111001", VLC_AC'length);
            when X"23" =>
              VLC_AC_size <= to_unsigned(10, VLC_AC_size'length);
              VLC_AC      <= resize("1111110111", VLC_AC'length);
            when X"24" =>
              VLC_AC_size <= to_unsigned(12, VLC_AC_size'length);
              VLC_AC      <= resize("111111110100", VLC_AC'length);
            when X"25" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110001001", VLC_AC'length);
            when X"26" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110001010", VLC_AC'length);
            when X"27" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110001011", VLC_AC'length);
            when X"28" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110001100", VLC_AC'length);
            when X"29" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110001101", VLC_AC'length);
            when X"2A" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110001110", VLC_AC'length);
            when X"31" =>
              VLC_AC_size <= to_unsigned(6, VLC_AC_size'length);
              VLC_AC      <= resize("111010", VLC_AC'length);
            when X"32" =>
              VLC_AC_size <= to_unsigned(9, VLC_AC_size'length);
              VLC_AC      <= resize("111110111", VLC_AC'length);
            when X"33" =>
              VLC_AC_size <= to_unsigned(12, VLC_AC_size'length);
              VLC_AC      <= resize("111111110101", VLC_AC'length);
            when X"34" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110001111", VLC_AC'length);
            when X"35" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110010000", VLC_AC'length);
            when X"36" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110010001", VLC_AC'length);
            when X"37" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110010010", VLC_AC'length);
            when X"38" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110010011", VLC_AC'length);
            when X"39" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110010100", VLC_AC'length);
            when X"3A" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110010101", VLC_AC'length);
            when X"41" =>
              VLC_AC_size <= to_unsigned(6, VLC_AC_size'length);
              VLC_AC      <= resize("111011", VLC_AC'length);
            when X"42" =>
              VLC_AC_size <= to_unsigned(10, VLC_AC_size'length);
              VLC_AC      <= resize("1111111000", VLC_AC'length);
            when X"43" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110010110", VLC_AC'length);
            when X"44" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110010111", VLC_AC'length);
            when X"45" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110011000", VLC_AC'length);
            when X"46" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110011001", VLC_AC'length);
            when X"47" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110011010", VLC_AC'length);
            when X"48" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110011011", VLC_AC'length);
            when X"49" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110011100", VLC_AC'length);
            when X"4A" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110011101", VLC_AC'length);
            when X"51" =>
              VLC_AC_size <= to_unsigned(7, VLC_AC_size'length);
              VLC_AC      <= resize("1111010", VLC_AC'length);
            when X"52" =>
              VLC_AC_size <= to_unsigned(11, VLC_AC_size'length);
              VLC_AC      <= resize("11111110111", VLC_AC'length);
            when X"53" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110011110", VLC_AC'length);
            when X"54" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110011111", VLC_AC'length);
            when X"55" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110100000", VLC_AC'length);
            when X"56" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110100001", VLC_AC'length);
            when X"57" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110100010", VLC_AC'length);
            when X"58" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110100011", VLC_AC'length);
            when X"59" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110100100", VLC_AC'length);
            when X"5A" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110100101", VLC_AC'length);
            when X"61" =>
              VLC_AC_size <= to_unsigned(7, VLC_AC_size'length);
              VLC_AC      <= resize("1111011", VLC_AC'length);
            when X"62" =>
              VLC_AC_size <= to_unsigned(12, VLC_AC_size'length);
              VLC_AC      <= resize("111111110110", VLC_AC'length);
            when X"63" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110100110", VLC_AC'length);
            when X"64" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110100111", VLC_AC'length);
            when X"65" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110101000", VLC_AC'length);
            when X"66" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110101001", VLC_AC'length);
            when X"67" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110101010", VLC_AC'length);
            when X"68" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110101011", VLC_AC'length);
            when X"69" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110101100", VLC_AC'length);
            when X"6A" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110101101", VLC_AC'length);
            when X"71" =>
              VLC_AC_size <= to_unsigned(8, VLC_AC_size'length);
              VLC_AC      <= resize("11111010", VLC_AC'length);
            when X"72" =>
              VLC_AC_size <= to_unsigned(12, VLC_AC_size'length);
              VLC_AC      <= resize("111111110111", VLC_AC'length);
            when X"73" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110101110", VLC_AC'length);
            when X"74" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110101111", VLC_AC'length);
            when X"75" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110110000", VLC_AC'length);
            when X"76" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110110001", VLC_AC'length);
            when X"77" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110110010", VLC_AC'length);
            when X"78" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110110011", VLC_AC'length);
            when X"79" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110110100", VLC_AC'length);
            when X"7A" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110110101", VLC_AC'length);
            when X"81" =>
              VLC_AC_size <= to_unsigned(9, VLC_AC_size'length);
              VLC_AC      <= resize("111111000", VLC_AC'length);
            when X"82" =>
              VLC_AC_size <= to_unsigned(15, VLC_AC_size'length);
              VLC_AC      <= resize("111111111000000", VLC_AC'length);
            when X"83" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110110110", VLC_AC'length);
            when X"84" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110110111", VLC_AC'length);
            when X"85" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110111000", VLC_AC'length);
            when X"86" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110111001", VLC_AC'length);
            when X"87" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110111010", VLC_AC'length);
            when X"88" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110111011", VLC_AC'length);
            when X"89" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110111100", VLC_AC'length);
            when X"8A" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110111101", VLC_AC'length);
            when X"91" =>
              VLC_AC_size <= to_unsigned(9, VLC_AC_size'length);
              VLC_AC      <= resize("111111001", VLC_AC'length);
            when X"92" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110111110", VLC_AC'length);
            when X"93" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111110111111", VLC_AC'length);
            when X"94" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111000000", VLC_AC'length);
            when X"95" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111000001", VLC_AC'length);
            when X"96" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111000010", VLC_AC'length);
            when X"97" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111000011", VLC_AC'length);
            when X"98" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111000100", VLC_AC'length);
            when X"99" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111000101", VLC_AC'length);
            when X"9A" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111000110", VLC_AC'length);
            when X"A1" =>
              VLC_AC_size <= to_unsigned(9, VLC_AC_size'length);
              VLC_AC      <= resize("111111010", VLC_AC'length);
            when X"A2" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111000111", VLC_AC'length);
            when X"A3" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111001000", VLC_AC'length);
            when X"A4" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111001001", VLC_AC'length);
            when X"A5" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111001010", VLC_AC'length);
            when X"A6" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111001011", VLC_AC'length);
            when X"A7" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111001100", VLC_AC'length);
            when X"A8" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111001101", VLC_AC'length);
            when X"A9" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111001110", VLC_AC'length);
            when X"AA" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111001111", VLC_AC'length);
            when X"B1" =>
              VLC_AC_size <= to_unsigned(10, VLC_AC_size'length);
              VLC_AC      <= resize("1111111001", VLC_AC'length);
            when X"B2" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111010000", VLC_AC'length);
            when X"B3" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111010001", VLC_AC'length);
            when X"B4" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111010010", VLC_AC'length);
            when X"B5" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111010011", VLC_AC'length);
            when X"B6" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111010100", VLC_AC'length);
            when X"B7" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111010101", VLC_AC'length);
            when X"B8" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111010110", VLC_AC'length);
            when X"B9" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111010111", VLC_AC'length);
            when X"BA" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111011000", VLC_AC'length);
            when X"C1" =>
              VLC_AC_size <= to_unsigned(10, VLC_AC_size'length);
              VLC_AC      <= resize("1111111010", VLC_AC'length);
            when X"C2" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111011001", VLC_AC'length);
            when X"C3" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111011010", VLC_AC'length);
            when X"C4" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111011011", VLC_AC'length);
            when X"C5" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111011100", VLC_AC'length);
            when X"C6" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111011101", VLC_AC'length);
            when X"C7" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111011110", VLC_AC'length);
            when X"C8" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111011111", VLC_AC'length);
            when X"C9" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111100000", VLC_AC'length);
            when X"CA" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111100001", VLC_AC'length);
            when X"D1" =>
              VLC_AC_size <= to_unsigned(11, VLC_AC_size'length);
              VLC_AC      <= resize("11111111000", VLC_AC'length);
            when X"D2" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111100010", VLC_AC'length);
            when X"D3" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111100011", VLC_AC'length);
            when X"D4" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111100100", VLC_AC'length);
            when X"D5" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111100101", VLC_AC'length);
            when X"D6" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111100110", VLC_AC'length);
            when X"D7" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111100111", VLC_AC'length);
            when X"D8" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111101000", VLC_AC'length);
            when X"D9" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111101001", VLC_AC'length);
            when X"DA" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111101010", VLC_AC'length);
            when X"E1" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111101011", VLC_AC'length);
            when X"E2" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111101100", VLC_AC'length);
            when X"E3" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111101101", VLC_AC'length);
            when X"E4" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111101110", VLC_AC'length);
            when X"E5" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111101111", VLC_AC'length);
            when X"E6" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111110000", VLC_AC'length);
            when X"E7" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111110001", VLC_AC'length);
            when X"E8" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111110010", VLC_AC'length);
            when X"E9" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111110011", VLC_AC'length);
            when X"EA" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111110100", VLC_AC'length);
            when X"F0" =>
              VLC_AC_size <= to_unsigned(11, VLC_AC_size'length);
              VLC_AC      <= resize("11111111001", VLC_AC'length);
            when X"F1" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111110101", VLC_AC'length);
            when X"F2" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111110110", VLC_AC'length);
            when X"F3" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111110111", VLC_AC'length);
            when X"F4" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111111000", VLC_AC'length);
            when X"F5" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111111001", VLC_AC'length);
            when X"F6" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111111010", VLC_AC'length);
            when X"F7" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111111011", VLC_AC'length);
            when X"F8" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111111100", VLC_AC'length);
            when X"F9" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111111101", VLC_AC'length);
            when X"FA" =>
              VLC_AC_size <= to_unsigned(16, VLC_AC_size'length);
              VLC_AC      <= resize("1111111111111110", VLC_AC'length);
            when others =>
              VLC_AC_size <= to_unsigned(0, VLC_AC_size'length);
              VLC_AC      <= resize("0", VLC_AC'length);
          end case;
    end if;
  end process;



end architecture RTL;
-------------------------------------------------------------------------------
-- Architecture: end
-------------------------------------------------------------------------------