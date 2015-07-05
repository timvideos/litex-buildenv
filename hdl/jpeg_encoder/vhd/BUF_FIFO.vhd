-------------------------------------------------------------------------------
-- File Name : BUF_FIFO.vhd
--
-- Project   : JPEG_ENC
--
-- Module    : BUF_FIFO
--
-- Content   : Input FIFO Buffer
--
-- Description : 
--
-- Spec.     : 
--
-- Author    : Michal Krepa
--
-------------------------------------------------------------------------------
-- History :
-- 20090311: (MK): Initial Creation.
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
library work;
  use work.JPEG_PKG.all;
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
----------------------------------- ENTITY ------------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
entity BUF_FIFO is
  port 
  (
        CLK                : in  std_logic;
        RST                : in  std_logic;
        -- HOST PROG
        img_size_x         : in  std_logic_vector(15 downto 0);
        img_size_y         : in  std_logic_vector(15 downto 0);
        sof                : in  std_logic;
        
        -- HOST DATA
        iram_wren          : in  std_logic;
        iram_wdata         : in  std_logic_vector(C_PIXEL_BITS-1 downto 0);
        fifo_almost_full   : out std_logic;
        
        -- FDCT
        fdct_fifo_rd       : in  std_logic;
        fdct_fifo_q        : out std_logic_vector(23 downto 0);
        fdct_fifo_hf_full  : out std_logic
    );
end entity BUF_FIFO;

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
----------------------------------- ARCHITECTURE ------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
architecture RTL of BUF_FIFO is

  
  constant C_NUM_LINES    : integer := 8 + C_EXTRA_LINES;

  signal pixel_cnt        : unsigned(15 downto 0):=(others=>'0');
  signal line_cnt         : unsigned(15 downto 0):=(others=>'0');

  signal ramq             : STD_LOGIC_VECTOR(C_PIXEL_BITS-1 downto 0):=(others=>'0');
  signal ramd             : STD_LOGIC_VECTOR(C_PIXEL_BITS-1 downto 0):=(others=>'0');
  signal ramwaddr         : unsigned(log2(C_MAX_LINE_WIDTH*C_NUM_LINES)-1 downto 0):=(others=>'0');
  signal ramenw           : STD_LOGIC:='0';
  signal ramraddr         : unsigned(log2(C_MAX_LINE_WIDTH*C_NUM_LINES)-1 downto 0):=(others=>'0');
  
  signal pix_inblk_cnt    : unsigned(3 downto 0):=(others=>'0');
  signal pix_inblk_cnt_d1 : unsigned(3 downto 0):=(others=>'0');
  signal line_inblk_cnt   : unsigned(2 downto 0):=(others=>'0');
  
  signal read_block_cnt   : unsigned(12 downto 0):=(others=>'0');
  signal read_block_cnt_d1 : unsigned(12 downto 0):=(others=>'0');
  signal write_block_cnt  : unsigned(12 downto 0):=(others=>'0');
  
  signal ramraddr_int     : unsigned(16+log2(C_NUM_LINES)-1 downto 0):=(others=>'0');
  signal raddr_base_line  : unsigned(16+log2(C_NUM_LINES)-1 downto 0):=(others=>'0');
  signal raddr_tmp        : unsigned(15 downto 0):=(others=>'0');
  signal ramwaddr_d1      : unsigned(ramwaddr'range):=(others=>'0');
  
  signal line_lock        : unsigned(log2(C_NUM_LINES)-1 downto 0):=(others=>'0');
  
  signal memwr_line_cnt   : unsigned(log2(C_NUM_LINES)-1 downto 0):=(others=>'0');
  
  signal memrd_offs_cnt   : unsigned(log2(C_NUM_LINES)-1+1 downto 0):=(others=>'0');
  signal memrd_line       : unsigned(log2(C_NUM_LINES)-1 downto 0):=(others=>'0');
  
  signal wr_line_idx      : unsigned(15 downto 0):=(others=>'0');
  signal rd_line_idx      : unsigned(15 downto 0):=(others=>'0');
  
  signal image_write_end  : std_logic:='0';  
  
  
  
-------------------------------------------------------------------------------
-- Architecture: begin
-------------------------------------------------------------------------------
begin  
  -------------------------------------------------------------------
  -- RAM for SUB_FIFOs
  -------------------------------------------------------------------
  U_SUB_RAMZ : entity work.SUB_RAMZ
  generic map 
  (
           RAMADDR_W => log2( C_MAX_LINE_WIDTH*C_NUM_LINES ),
           RAMDATA_W => C_PIXEL_BITS        
  )   
  port map 
  (      
        d            => ramd,               
        waddr        => std_logic_vector(ramwaddr_d1),     
        raddr        => std_logic_vector(ramraddr),     
        we           => ramenw,     
        clk          => clk,     
        
        q            => ramq     
  ); 
  
  -------------------------------------------------------------------
  -- register RAM data input
  -------------------------------------------------------------------
  p_mux1 : process(CLK, RST)
  begin
    if RST = '1' then
      ramenw           <= '0';
      ramd             <= (others => '0');
    elsif CLK'event and CLK = '1' then
      ramd      <= iram_wdata;
      ramenw    <= iram_wren;
    end if;
  end process;
  
  -------------------------------------------------------------------
  -- resolve RAM write address
  -------------------------------------------------------------------
  p_pixel_cnt : process(CLK, RST)
  begin
    if RST = '1' then
      pixel_cnt      <= (others => '0');
      memwr_line_cnt <= (others => '0');
      wr_line_idx    <= (others => '0');
      ramwaddr       <= (others => '0');
      ramwaddr_d1    <= (others => '0');    
      image_write_end <= '0';
    elsif CLK'event and CLK = '1' then
      ramwaddr_d1 <= ramwaddr;
    
      if iram_wren = '1' then
        -- end of line
        if pixel_cnt = unsigned(img_size_x)-1 then
          pixel_cnt <= (others => '0');
          -- absolute write line index
          wr_line_idx <= wr_line_idx + 1;
          
          if wr_line_idx = unsigned(img_size_y)-1 then
            image_write_end <= '1';
          end if;
          
          -- memory line index
          if memwr_line_cnt = C_NUM_LINES-1 then
            memwr_line_cnt <= (others => '0');
            ramwaddr       <= (others => '0');
          else         
            memwr_line_cnt <= memwr_line_cnt + 1;
            ramwaddr       <= ramwaddr + 1;
          end if;
        else
          pixel_cnt <= pixel_cnt + 1;
          ramwaddr  <= ramwaddr + 1;
        end if;  
      end if;
      
      if sof = '1' then
        pixel_cnt      <= (others => '0');
        ramwaddr       <= (others => '0');
        memwr_line_cnt <= (others => '0');
        wr_line_idx    <= (others => '0');
        image_write_end <= '0';
      end if;
    end if;
  end process;
  
  -------------------------------------------------------------------
  -- FIFO half full / almost full flag generation
  -------------------------------------------------------------------
  p_mux3 : process(CLK, RST)
  begin
    if RST = '1' then
      fdct_fifo_hf_full   <= '0';
      fifo_almost_full    <= '0';
    elsif CLK'event and CLK = '1' then
        
      if rd_line_idx + 8 <= wr_line_idx then
        fdct_fifo_hf_full <= '1';
      else
        fdct_fifo_hf_full <= '0';
      end if;
      
      fifo_almost_full <= '0';
      if wr_line_idx = rd_line_idx + C_NUM_LINES-1 then
        if pixel_cnt >= unsigned(img_size_x)-1-1 then
          fifo_almost_full <= '1';
        end if;
      elsif wr_line_idx > rd_line_idx + C_NUM_LINES-1 then
        fifo_almost_full <= '1';
      end if;

      
    end if;
  end process;
  
  -------------------------------------------------------------------
  -- read side
  -------------------------------------------------------------------
  p_mux5 : process(CLK, RST)
  begin
    if RST = '1' then
      memrd_offs_cnt <= (others => '0');
      read_block_cnt <= (others => '0');
      pix_inblk_cnt  <= (others => '0');
      line_inblk_cnt <= (others => '0');
      rd_line_idx    <= (others => '0');
      pix_inblk_cnt_d1  <= (others => '0');
      read_block_cnt_d1 <= (others => '0');
    elsif CLK'event and CLK = '1' then
      pix_inblk_cnt_d1 <= pix_inblk_cnt;
      read_block_cnt_d1 <= read_block_cnt;
      
      -- BUF FIFO read
      if fdct_fifo_rd = '1' then
        -- last pixel in block
        if pix_inblk_cnt = 8-1 then
          pix_inblk_cnt <= (others => '0');

          -- last line in 8
          if line_inblk_cnt = 8-1 then
            line_inblk_cnt <= (others => '0');

            -- last block in last line
            if read_block_cnt = unsigned(img_size_x(15 downto 3))-1 then
              read_block_cnt <= (others => '0');
              rd_line_idx <= rd_line_idx + 8;
              if memrd_offs_cnt + 8 > C_NUM_LINES-1 then
                memrd_offs_cnt <= memrd_offs_cnt + 8 - C_NUM_LINES;
              else
                memrd_offs_cnt <= memrd_offs_cnt + 8;
              end if;
            else
              read_block_cnt <= read_block_cnt + 1;
            end if;
          else
            line_inblk_cnt <= line_inblk_cnt + 1;
          end if;
          
        else
          pix_inblk_cnt <= pix_inblk_cnt + 1;
        end if;
      end if;
      
      if memrd_offs_cnt + (line_inblk_cnt) > C_NUM_LINES-1 then
        memrd_line <= memrd_offs_cnt(memrd_line'range) + (line_inblk_cnt) - (C_NUM_LINES);
      else
        memrd_line <= memrd_offs_cnt(memrd_line'range) + (line_inblk_cnt);
      end if;
      
      if sof = '1' then
        memrd_line     <= (others => '0');
        memrd_offs_cnt <= (others => '0');
        read_block_cnt <= (others => '0');
        pix_inblk_cnt  <= (others => '0');
        line_inblk_cnt <= (others => '0');
        rd_line_idx    <= (others => '0');
      end if;
      
    end if;
  end process;
  
  -- generate RAM data output based on 16 or 24 bit mode selection
  fdct_fifo_q <= (ramq(15 downto 11) & "000" & 
                 ramq(10 downto 5) & "00" & 
                 ramq(4 downto 0) & "000") when C_PIXEL_BITS = 16 else 
                 std_logic_vector(resize(unsigned(ramq), 24));
  
  
  ramraddr <= ramraddr_int(ramraddr'range);
  
  -------------------------------------------------------------------
  -- resolve RAM read address
  -------------------------------------------------------------------
  p_mux4 : process(CLK, RST)
  begin
    if RST = '1' then
      ramraddr_int          <= (others => '0');
    elsif CLK'event and CLK = '1' then
      raddr_base_line <= (memrd_line) * unsigned(img_size_x);
      raddr_tmp       <= (read_block_cnt_d1 & "000") + pix_inblk_cnt_d1;
    
      ramraddr_int <= raddr_tmp + raddr_base_line;
    end if;
  end process;

end architecture RTL;
-------------------------------------------------------------------------------
-- Architecture: end
-------------------------------------------------------------------------------