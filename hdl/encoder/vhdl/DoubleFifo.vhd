-------------------------------------------------------------------------------
-- File Name :  DoubleFifo.vhd
--
-- Project   : JPEG_ENC
--
-- Module    : DoubleFifo
--
-- Content   : DoubleFifo
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
entity DoubleFifo is
  port 
  (
        CLK                : in  std_logic;
        RST                : in  std_logic;
        -- HUFFMAN
        data_in            : in  std_logic_vector(7 downto 0);
        wren               : in  std_logic;
        -- BYTE STUFFER
        buf_sel            : in  std_logic;
        rd_req             : in  std_logic;
        fifo_empty         : out std_logic;
        data_out           : out std_logic_vector(7 downto 0)
    );
end entity DoubleFifo;

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
----------------------------------- ARCHITECTURE ------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
architecture RTL of DoubleFifo is

  signal fifo1_rd      : std_logic;
  signal fifo1_wr      : std_logic;
  signal fifo1_q       : std_logic_vector(7 downto 0);
  signal fifo1_full    : std_logic;
  signal fifo1_empty   : std_logic;
  signal fifo1_count   : std_logic_vector(7 downto 0);
  
  signal fifo2_rd      : std_logic;
  signal fifo2_wr      : std_logic;
  signal fifo2_q       : std_logic_vector(7 downto 0);
  signal fifo2_full    : std_logic;
  signal fifo2_empty   : std_logic;
  signal fifo2_count   : std_logic_vector(7 downto 0);
  
  signal fifo_data_in  : std_logic_vector(7 downto 0);
-------------------------------------------------------------------------------
-- Architecture: begin
-------------------------------------------------------------------------------
begin
  
  -------------------------------------------------------------------
  -- FIFO 1
  -------------------------------------------------------------------
  U_FIFO_1 : entity work.FIFO   
  generic map
  (
        DATA_WIDTH        => 8,
        ADDR_WIDTH        => 7
  )
  port map 
  (        
        rst               => RST,
        clk               => CLK,
        rinc              => fifo1_rd,
        winc              => fifo1_wr,
        datai             => fifo_data_in,

        datao             => fifo1_q,
        fullo             => fifo1_full,
        emptyo            => fifo1_empty,
        count             => fifo1_count
  );
  
  -------------------------------------------------------------------
  -- FIFO 2
  -------------------------------------------------------------------
  U_FIFO_2 : entity work.FIFO   
  generic map
  (
        DATA_WIDTH        => 8,
        ADDR_WIDTH        => 7
  )
  port map 
  (        
        rst               => RST,
        clk               => CLK,
        rinc              => fifo2_rd,
        winc              => fifo2_wr,
        datai             => fifo_data_in,

        datao             => fifo2_q,
        fullo             => fifo2_full,
        emptyo            => fifo2_empty,
        count             => fifo2_count
  );
  
  -------------------------------------------------------------------
  -- mux2
  -------------------------------------------------------------------
  p_mux2 : process(CLK, RST)
  begin
    if RST = '1' then
      fifo1_wr <= '0';
      fifo2_wr <= '0';
      fifo_data_in <= (others => '0');
    elsif CLK'event and CLK = '1' then
      if buf_sel = '0' then
        fifo1_wr <= wren;
      else
        fifo2_wr <= wren;
      end if;
      fifo_data_in <= data_in;
    end if;
  end process;
  
  -------------------------------------------------------------------
  -- mux3
  -------------------------------------------------------------------
  p_mux3 : process(CLK, RST)
  begin
    if RST = '1' then
      data_out   <= (others => '0');
      fifo1_rd   <= '0';
      fifo2_rd   <= '0';
      fifo_empty <= '0';
    elsif CLK'event and CLK = '1' then
      if buf_sel = '1' then
        data_out   <= fifo1_q;
        fifo1_rd   <= rd_req;
        fifo_empty <= fifo1_empty;
      else
        data_out <= fifo2_q;
        fifo2_rd <= rd_req;
        fifo_empty <= fifo2_empty;
      end if;
    end if;
  end process;
  

end architecture RTL;
-------------------------------------------------------------------------------
-- Architecture: end
-------------------------------------------------------------------------------