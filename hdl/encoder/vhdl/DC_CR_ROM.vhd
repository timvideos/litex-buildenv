-------------------------------------------------------------------------------
-- File Name :  DC_CR_ROM.vhd
--
-- Project   : JPEG_ENC
--
-- Module    : DC_CR_ROM
--
-- Content   : DC_CR_ROM Chrominance
--
-- Description : 
--
-- Spec.     : 
--
-- Author    : Michal Krepa
--
-------------------------------------------------------------------------------
-- History :
-- 20090329: (MK): Initial Creation.
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
entity DC_CR_ROM is
  port 
  (
        CLK                : in  std_logic;
        RST                : in  std_logic;
        VLI_size           : in  std_logic_vector(3 downto 0);
        
        VLC_DC_size        : out std_logic_vector(3 downto 0);
        VLC_DC             : out unsigned(10 downto 0)        
    );
end entity DC_CR_ROM;

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
----------------------------------- ARCHITECTURE ------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
architecture RTL of DC_CR_ROM is

  
  
-------------------------------------------------------------------------------
-- Architecture: begin
-------------------------------------------------------------------------------
begin

  -------------------------------------------------------------------
  -- DC-ROM
  -------------------------------------------------------------------
  p_DC_CR_ROM : process(CLK, RST)
  begin
    if RST = '1' then
      VLC_DC_size <= X"0";
      VLC_DC      <= (others => '0'); 
    elsif CLK'event and CLK = '1' then
      case VLI_size is 
        when X"0" =>
          VLC_DC_size <= X"2";
          VLC_DC      <= resize("00", VLC_DC'length); 
        when X"1" =>
          VLC_DC_size <= X"2";
          VLC_DC      <= resize("01", VLC_DC'length); 
        when X"2" =>
          VLC_DC_size <= X"2";
          VLC_DC      <= resize("10", VLC_DC'length); 
        when X"3" =>
          VLC_DC_size <= X"3";
          VLC_DC      <= resize("110", VLC_DC'length); 
        when X"4" =>
          VLC_DC_size <= X"4";
          VLC_DC      <= resize("1110", VLC_DC'length); 
        when X"5" =>
          VLC_DC_size <= X"5";
          VLC_DC      <= resize("11110", VLC_DC'length); 
        when X"6" =>
          VLC_DC_size <= X"6";
          VLC_DC      <= resize("111110", VLC_DC'length); 
        when X"7" =>
          VLC_DC_size <= X"7";
          VLC_DC      <= resize("1111110", VLC_DC'length); 
        when X"8" =>
          VLC_DC_size <= X"8";
          VLC_DC      <= resize("11111110", VLC_DC'length); 
        when X"9" =>
          VLC_DC_size <= X"9";
          VLC_DC      <= resize("111111110", VLC_DC'length); 
        when X"A" =>
          VLC_DC_size <= X"A";
          VLC_DC      <= resize("1111111110", VLC_DC'length); 
        when X"B" =>
          VLC_DC_size <= X"B";
          VLC_DC      <= resize("11111111110", VLC_DC'length); 
        when others =>
          VLC_DC_size <= X"0";
          VLC_DC      <= (others => '0'); 
      end case;
    end if;
  end process;
  
  

end architecture RTL;
-------------------------------------------------------------------------------
-- Architecture: end
-------------------------------------------------------------------------------