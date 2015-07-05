-------------------------------------------------------------------------------
-- File Name :  SingleSM.vhd
--
-- Project   : 
--
-- Module    :
--
-- Content   : 
--
-- Description : 
--
-- Spec.     : 
--
-- Author    : Michal Krepa
-------------------------------------------------------------------------------
-- History :
-- 20080301: (MK): Initial Creation.
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
library ieee;
  use ieee.std_logic_1164.all;

entity SingleSM is
  port 
  (
        CLK                : in  std_logic;
        RST                : in  std_logic;
        -- from/to SM(m)
        start_i            : in  std_logic;
        idle_o             : out std_logic;
        -- from/to SM(m+1)
        idle_i             : in  std_logic;
        start_o            : out std_logic;
        -- from/to processing block
        pb_rdy_i           : in  std_logic;
        pb_start_o         : out std_logic;
        -- state debug
        fsm_o              : out std_logic_vector(1 downto 0)
    );
end entity SingleSM;   

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
----------------------------------- ARCHITECTURE ------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
architecture SingleSM_rtl of SingleSM is


-------------------------------------------------------------------------------
-- Architecture: Signal definition.
-------------------------------------------------------------------------------
  type T_STATE is (IDLE, WAIT_FOR_BLK_RDY, WAIT_FOR_BLK_IDLE);
  
  signal state : T_STATE;
  
-------------------------------------------------------------------------------
-- Architecture: begin
-------------------------------------------------------------------------------
begin

  fsm_o <= "00" when state = IDLE else
           "01" when state = WAIT_FOR_BLK_RDY else
           "10" when state = WAIT_FOR_BLK_IDLE else
           "11";

  ------------------------------------------------------------------------------
  -- FSM
  ------------------------------------------------------------------------------
  p_fsm : process(CLK, RST)
  begin
    if RST = '1' then
      idle_o     <= '0';
      start_o    <= '0';
      pb_start_o <= '0';
      state      <= IDLE;
    elsif CLK'event and CLK = '1' then
      idle_o     <= '0';
      start_o    <= '0';
      pb_start_o <= '0';
    
      case state is
        when IDLE =>
          idle_o <= '1';
          -- this fsm is started
          if start_i = '1' then
            state      <= WAIT_FOR_BLK_RDY;
            -- start processing block associated with this FSM
            pb_start_o <= '1';
            idle_o     <= '0';
          end if;       
        
        when WAIT_FOR_BLK_RDY =>
          -- wait until processing block completes
          if pb_rdy_i = '1' then
            -- wait until next FSM is idle before starting it
            if idle_i = '1' then
              state   <= IDLE;
              start_o <= '1';
            else
              state <= WAIT_FOR_BLK_IDLE;
            end if;
          end if;
        
        when WAIT_FOR_BLK_IDLE =>
          if idle_i = '1' then
            state   <= IDLE;
            start_o <= '1';
          end if;
        
        when others =>
          idle_o     <= '0';
          start_o    <= '0';
          pb_start_o <= '0';
          state      <= IDLE;
        
      end case;
      
    end if;
  end process;

end architecture SingleSM_rtl;
-------------------------------------------------------------------------------
-- Architecture: end
-------------------------------------------------------------------------------
