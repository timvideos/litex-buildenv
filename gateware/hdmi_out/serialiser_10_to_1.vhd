----------------------------------------------------------------------------------
-- File: serialiser_10_to_1.vhd
--
-- Engineer:  Mike Field <hamster@snap.net.nz> 
-- 
-- Module Name: serialiser_10_to_1 - Behavioral
--
-- Description: Using the OSERDESE2 as a 10:1 serialiser, using a x1 and x5
--              clocks (using DDR outputs).
--
-- The tricky bit is that reset needs to be asserted, and then CE asserted 
-- after the reset or it will not simulate correctly (outputs show as 'X') 
-- 
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
library UNISIM;
use UNISIM.VComponents.all;

entity serialiser_10_to_1 is
    Port ( clk    : in STD_LOGIC;
           clk_x5 : in STD_LOGIC;
           data   : in STD_LOGIC_VECTOR (9 downto 0);
           reset  : in std_logic;
           serial : out STD_LOGIC);
end serialiser_10_to_1;

architecture Behavioral of serialiser_10_to_1 is
    signal shift1      : std_logic := '0';
    signal shift2      : std_logic := '0';
    signal ce_delay    : std_logic := '0';
    signal reset_delay : std_logic_vector(7 downto 0) := (others => '0');
begin

master_serdes : OSERDESE2
   generic map (
      DATA_RATE_OQ => "DDR",   -- DDR, SDR
      DATA_RATE_TQ => "DDR",   -- DDR, BUF, SDR
      DATA_WIDTH => 10,         -- Parallel data width (2-8,10,14)
      INIT_OQ => '1',          -- Initial value of OQ output (1'b0,1'b1)
      INIT_TQ => '1',          -- Initial value of TQ output (1'b0,1'b1)
      SERDES_MODE => "MASTER", -- MASTER, SLAVE
      SRVAL_OQ => '0',         -- OQ output value when SR is used (1'b0,1'b1)
      SRVAL_TQ => '0',         -- TQ output value when SR is used (1'b0,1'b1)
      TBYTE_CTL => "FALSE",    -- Enable tristate byte operation (FALSE, TRUE)
      TBYTE_SRC => "FALSE",    -- Tristate byte source (FALSE, TRUE)
      TRISTATE_WIDTH => 1      -- 3-state converter width (1,4)
   )
   port map (
      OFB       => open,             -- 1-bit output: Feedback path for data
      OQ        => serial,               -- 1-bit output: Data path output
      -- SHIFTOUT1 / SHIFTOUT2: 1-bit (each) output: Data output expansion (1-bit each)
      SHIFTOUT1 => open,
      SHIFTOUT2 => open,
      TBYTEOUT  => open,   -- 1-bit output: Byte group tristate
      TFB       => open,             -- 1-bit output: 3-state control
      TQ        => open,               -- 1-bit output: 3-state control
      CLK       => clk_x5,             -- 1-bit input: High speed clock
      CLKDIV    => clk,       -- 1-bit input: Divided clock
      -- D1 - D8: 1-bit (each) input: Parallel data inputs (1-bit each)
      D1 => data(0),
      D2 => data(1),
      D3 => data(2),
      D4 => data(3),
      D5 => data(4),
      D6 => data(5),
      D7 => data(6),
      D8 => data(7),
      OCE => ce_delay,             -- 1-bit input: Output data clock enable
      RST => reset,             -- 1-bit input: Reset
      -- SHIFTIN1 / SHIFTIN2: 1-bit (each) input: Data input expansion (1-bit each)
      SHIFTIN1 => SHIFT1,
      SHIFTIN2 => SHIFT2,
      -- T1 - T4: 1-bit (each) input: Parallel 3-state inputs
      T1 => '0',
      T2 => '0',
      T3 => '0',
      T4 => '0',
      TBYTEIN => '0', -- 1-bit input: Byte group tristate
      TCE => '0'                  -- 1-bit input: 3-state clock enable
   );

slave_serdes : OSERDESE2
   generic map (
      DATA_RATE_OQ   => "DDR",   -- DDR, SDR
      DATA_RATE_TQ   => "DDR",   -- DDR, BUF, SDR
      DATA_WIDTH     => 10,      -- Parallel data width (2-8,10,14)
      INIT_OQ        => '1',     -- Initial value of OQ output (1'b0,1'b1)
      INIT_TQ        => '1',     -- Initial value of TQ output (1'b0,1'b1)
      SERDES_MODE    => "SLAVE", -- MASTER, SLAVE
      SRVAL_OQ       => '0',     -- OQ output value when SR is used (1'b0,1'b1)
      SRVAL_TQ       => '0',     -- TQ output value when SR is used (1'b0,1'b1)
      TBYTE_CTL      => "FALSE", -- Enable tristate byte operation (FALSE, TRUE)
      TBYTE_SRC      => "FALSE", -- Tristate byte source (FALSE, TRUE)
      TRISTATE_WIDTH => 1        -- 3-state converter width (1,4)
   )
   port map (
      OFB       => open,         -- 1-bit output: Feedback path for data
      OQ        => open,         -- 1-bit output: Data path output
      -- SHIFTOUT1 / SHIFTOUT2: 1-bit (each) output: Data output expansion (1-bit each)
      SHIFTOUT1 => shift1,
      SHIFTOUT2 => shift2,
      
      TBYTEOUT  => open,    -- 1-bit output: Byte group tristate
      TFB       => open,    -- 1-bit output: 3-state control
      TQ        => open,    -- 1-bit output: 3-state control
      CLK       => clk_x5,  -- 1-bit input: High speed clock
      CLKDIV    => clk,     -- 1-bit input: Divided clock
      -- D1 - D8: 1-bit (each) input: Parallel data inputs (1-bit each)
      D1       => '0',
      D2       => '0',
      D3       => data(8),
      D4       => data(9),
      D5       => '0',
      D6       => '0',
      D7       => '0',
      D8       => '0',
      OCE      => ce_delay,     -- 1-bit input: Output data clock enable
      RST      => reset,     -- 1-bit input: Reset
      -- SHIFTIN1 / SHIFTIN2: 1-bit (each) input: Data input expansion (1-bit each)
      SHIFTIN1 => '0',
      SHIFTIN2 => '0',
      -- T1 - T4: 1-bit (each) input: Parallel 3-state inputs
      T1       => '0',
      T2       => '0',
      T3       => '0',
      T4       => '0',
      TBYTEIN  => '0',     -- 1-bit input: Byte group tristate
      TCE      => '0'      -- 1-bit input: 3-state clock enable
   );
delay_ce: process(clk)
    begin
        if rising_edge(clk) then
            ce_delay <= not reset;
        end if;
    end process;
end Behavioral;
