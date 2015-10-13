--------------------------------------------------------------------------------
--                                                                            --
--                          V H D L    F I L E                                --
--                          COPYRIGHT (C) 2006                                --
--                                                                            --
--------------------------------------------------------------------------------
--
-- Title       : DCT
-- Design      : MDCT Core
-- Author      : Michal Krepa
--
--------------------------------------------------------------------------------
--
-- File        : ROME.VHD
-- Created     : Sat Mar 5 7:37 2006
--
--------------------------------------------------------------------------------
--
--  Description : ROM for DCT matrix constant cosine coefficients (even part)
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
-- 5:0
-- 5:4 = select matrix row (1 out of 4)
-- 3:0 = select precomputed MAC ( 1 out of 16)

library IEEE; 
  use IEEE.STD_LOGIC_1164.all;
  use IEEE.numeric_std.all;
  use WORK.MDCT_PKG.all;

entity ROME is 
  port( 
       addr         : in  STD_LOGIC_VECTOR(ROMADDR_W-1 downto 0); 
       clk          : in  STD_LOGIC; 
       
       datao        : out STD_LOGIC_VECTOR(ROMDATA_W-1 downto 0) 
  );         
  
end ROME; 

architecture RTL of ROME is  
  
  type ROM_TYPE is array (0 to (2**ROMADDR_W)-1) 
            of STD_LOGIC_VECTOR(ROMDATA_W-1 downto 0);
  constant rom : ROM_TYPE := 
    (
    (others => '0'),                
     std_logic_vector( to_signed(AP,          ROMDATA_W) ),
     std_logic_vector( to_signed(AP,          ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP,       ROMDATA_W) ),
     std_logic_vector( to_signed(AP,          ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP,       ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP,       ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP+AP,    ROMDATA_W) ),
     std_logic_vector( to_signed(AP,          ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP,       ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP,       ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP+AP,    ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP,       ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP+AP,    ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP+AP,    ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP+AP+AP, ROMDATA_W) ),

    -- 16
     (others => '0'),                
     std_logic_vector( to_signed(BM,    ROMDATA_W) ),
     std_logic_vector( to_signed(CM,    ROMDATA_W) ),
     std_logic_vector( to_signed(CM+BM, ROMDATA_W) ),
     std_logic_vector( to_signed(CP,    ROMDATA_W) ),
     std_logic_vector( to_signed(CP+BM, ROMDATA_W) ),
     (others => '0'),                
     std_logic_vector( to_signed(BM, ROMDATA_W) ),
     std_logic_vector( to_signed(BP, ROMDATA_W) ),
     (others => '0'),                
     std_logic_vector( to_signed(BP+CM, ROMDATA_W) ),
     std_logic_vector( to_signed(CM,    ROMDATA_W) ),
     std_logic_vector( to_signed(BP+CP, ROMDATA_W) ),
     std_logic_vector( to_signed(CP,    ROMDATA_W) ),
     std_logic_vector( to_signed(BP,    ROMDATA_W) ),
     (others => '0'),                

    
    -- 32
     (others => '0'),                
     std_logic_vector( to_signed(AP,    ROMDATA_W) ),
     std_logic_vector( to_signed(AM,    ROMDATA_W) ),
     (others => '0'),                
     std_logic_vector( to_signed(AM,    ROMDATA_W) ),
     (others => '0'),                
     std_logic_vector( to_signed(AM+AM, ROMDATA_W) ),
     std_logic_vector( to_signed(AM,    ROMDATA_W) ),
     std_logic_vector( to_signed(AP,    ROMDATA_W) ),
     std_logic_vector( to_signed(AP+AP, ROMDATA_W) ),
     (others => '0'),                
     std_logic_vector( to_signed(AP,    ROMDATA_W) ),
     (others => '0'),                
     std_logic_vector( to_signed(AP,    ROMDATA_W) ),
     std_logic_vector( to_signed(AM,    ROMDATA_W) ),
     (others => '0'),                

    
    -- 48                              
     (others => '0'),                
     std_logic_vector( to_signed(CM,    ROMDATA_W) ),
     std_logic_vector( to_signed(BP,    ROMDATA_W) ),
     std_logic_vector( to_signed(BP+CM, ROMDATA_W) ),
     std_logic_vector( to_signed(BM,    ROMDATA_W) ),
     std_logic_vector( to_signed(BM+CM, ROMDATA_W) ),
     (others => '0'),                
     std_logic_vector( to_signed(CM,    ROMDATA_W) ),
     std_logic_vector( to_signed(CP,    ROMDATA_W) ),
     (others => '0'),                
     std_logic_vector( to_signed(CP+BP, ROMDATA_W) ),
     std_logic_vector( to_signed(BP,    ROMDATA_W) ),
     std_logic_vector( to_signed(CP+BM, ROMDATA_W) ),
     std_logic_vector( to_signed(BM,    ROMDATA_W) ),
     std_logic_vector( to_signed(CP,    ROMDATA_W) ),
     (others => '0')
     );                
  
begin 

  
  process(clk)
  begin
    if rising_edge(clk) then
      datao <= rom(to_integer(unsigned(addr)) );
    end if;
  end process;  
      
end RTL;    

                

