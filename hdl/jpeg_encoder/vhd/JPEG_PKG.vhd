--------------------------------------------------------------------------------
--                                                                            --
--                          V H D L    F I L E                                --
--                          COPYRIGHT (C) 2009                                --
--                                                                            --
--------------------------------------------------------------------------------
--
-- Title       : JPEG_PKG
-- Design      : JPEG_ENC
-- Author      : Michal Krepa
--
--------------------------------------------------------------------------------
--
-- File        : JPEG_PKG.VHD
-- Created     : Sat Mar 7 2009
--
--------------------------------------------------------------------------------
--
--  Description : Package for JPEG core
--
--------------------------------------------------------------------------------
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
library IEEE;
  use IEEE.STD_LOGIC_1164.all;
  use ieee.numeric_std.all;
  
package JPEG_PKG is

  -- do not change, constant
  constant C_HDR_SIZE         : integer := 623;
  
  -- warning! this parameter heavily affects memory size required
  -- if expected image width is known change this parameter to match this
  -- otherwise some onchip RAM will be wasted and never used
  constant C_MAX_LINE_WIDTH   : integer := 1280;
  
  -- memory/performance tradeoff
  -- 8 extra lines highest performance
  -- 0 extra lines lowest area
  constant C_EXTRA_LINES  : integer := 8; -- from 0 to 8

  
  -- 24 bit format RGB 888 bits
  -- 16 bit format RGB 565 bits
  constant C_PIXEL_BITS    : integer := 24;
  
  type T_SM_SETTINGS is record
    x_cnt               : unsigned(15 downto 0);
    y_cnt               : unsigned(15 downto 0);
    cmp_idx             : unsigned(2 downto 0);
  end record;
  
  constant C_SM_SETTINGS : T_SM_SETTINGS := 
  (
    (others => '0'),
    (others => '0'),
    (others => '0')
  );
  
  function log2(n : natural) return natural;
  
end package JPEG_PKG;

package body JPEG_PKG is

  -----------------------------------------------------------------------------
  function log2(n : natural) 
  return natural is
  begin
    for i in 0 to 31 loop
      if (2**i) >= n then
        return i;
      end if;
    end loop;
    return 32;
  end log2;
  -----------------------------------------------------------------------------

end package body JPEG_PKG;