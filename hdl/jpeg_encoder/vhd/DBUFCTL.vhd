--------------------------------------------------------------------------------
--                                                                            --
--                          V H D L    F I L E                                --
--                          COPYRIGHT (C) 2006                                --
--                                                                            --
--------------------------------------------------------------------------------
--
-- Title       : DBUFCTL
-- Design      : MDCT Core
-- Author      : Michal Krepa
--
--------------------------------------------------------------------------------
--
-- File        : DBUFCTL.VHD
-- Created     : Thu Mar 30 22:19 2006
--
--------------------------------------------------------------------------------
--
--  Description : Double buffer memory controller
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

library WORK;
  use WORK.MDCT_PKG.all;

entity DBUFCTL is	
	port(	  
		clk          : in STD_LOGIC;  
		rst          : in STD_LOGIC;
    wmemsel      : in STD_LOGIC;
    rmemsel      : in STD_LOGIC;
    datareadyack : in STD_LOGIC;
      
    memswitchwr  : out STD_LOGIC;
    memswitchrd  : out STD_LOGIC;
    dataready    : out STD_LOGIC      
		);
end DBUFCTL;

architecture RTL of DBUFCTL is
 
  signal memswitchwr_reg : STD_LOGIC;
  signal memswitchrd_reg : STD_LOGIC;
  
begin

  memswitchwr  <= memswitchwr_reg;
  memswitchrd  <= memswitchrd_reg;
  
  memswitchrd_reg <= rmemsel;

  MEM_SWITCH : process(clk,rst)
  begin
    if rst = '1' then   
      memswitchwr_reg <= '0'; -- initially mem 1 is selected
      dataready       <= '0';
    elsif clk = '1' and clk'event then
      memswitchwr_reg <= wmemsel;
      
      if wmemsel /= memswitchwr_reg then
        dataready <= '1';
      end if;
      
      if datareadyack = '1' then
        dataready <= '0';
      end if;
    end if;
  end process;
  
end RTL;
--------------------------------------------------------------------------------