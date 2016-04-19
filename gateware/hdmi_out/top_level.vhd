-----------------------------------------------------------------------------
-- Project: Nexys Video 1080p - top level for testing
--
-- File : top_level.vhd
--
-- Author : Mike Field <hamster@snap.net.nz>
--
-- Date    : 30th June 2015
--
-----------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

Library UNISIM;
use UNISIM.vcomponents.all;

entity top_level is
    Port (
        clk100    : in STD_LOGIC;

        pixel_clk    : out std_logic;
        pixel_clk_x5 : out std_logic;
        reset        : out std_logic;

        vga_hsync  : out std_logic;
        vga_vsync  : out std_logic;
        vga_red    : out std_logic_vector(7 downto 0);
        vga_green  : out std_logic_vector(7 downto 0);
        vga_blue   : out std_logic_vector(7 downto 0);
        vga_blank  : out std_logic
);
end top_level;

architecture Behavioral of top_level is
    signal clk_pixel_x1  : std_logic;
    signal clk_pixel_x5  : std_logic;

    signal blank : std_logic := '0';
    signal hsync : std_logic := '0';
    signal vsync : std_logic := '0';

    component vga_gen_1080p is
        port (
           clk        : in  std_logic;

           blank      : out std_logic;
           hsync      : out std_logic;
           vsync      : out std_logic
           );
    end component;

    component vga_output is
        Port ( clk : in STD_LOGIC;
               hsync_in : in STD_LOGIC;
               vsync_in : in STD_LOGIC;
               blank_in : in STD_LOGIC;
               count     : in STD_LOGIC_VECTOR(7 downto 0);
               vga_hsync : out std_logic;
               vga_vsync : out std_logic;
               vga_red   : out std_logic_vector(7 downto 0);
               vga_green : out std_logic_vector(7 downto 0);
               vga_blue  : out std_logic_vector(7 downto 0);
               vga_blank : out std_logic);
    end component;

    signal count         : std_logic_vector(7 downto 0);

    signal locked        : std_logic;
    signal clkfb         : std_logic;
begin
    reset <= not locked;

MMCME2_BASE_inst : MMCME2_BASE
   generic map (
      BANDWIDTH => "OPTIMIZED",  -- Jitter programming (OPTIMIZED, HIGH, LOW)
      DIVCLK_DIVIDE   => 4,        -- Master division value (1-106)
      CLKFBOUT_MULT_F => 30.0,    -- Multiply value for all CLKOUT (2.000-64.000).
      CLKFBOUT_PHASE => 0.0,     -- Phase offset in degrees of CLKFB (-360.000-360.000).
      CLKIN1_PERIOD => 10.0,      -- Input clock period in ns to ps resolution (i.e. 33.333 is 30 MHz).
      -- CLKOUT0_DIVIDE - CLKOUT6_DIVIDE: Divide amount for each CLKOUT (1-128)
      CLKOUT0_DIVIDE_F => 5.0,   -- Divide amount for CLKOUT0 (1.000-128.000).
      CLKOUT1_DIVIDE   => 5,
      CLKOUT2_DIVIDE   => 1,
      CLKOUT3_DIVIDE   => 1,
      CLKOUT4_DIVIDE   => 1,
      CLKOUT5_DIVIDE   => 1,
      CLKOUT6_DIVIDE   => 1,
      -- CLKOUT0_DUTY_CYCLE - CLKOUT6_DUTY_CYCLE: Duty cycle for each CLKOUT (0.01-0.99).
      CLKOUT0_DUTY_CYCLE => 0.5,
      CLKOUT1_DUTY_CYCLE => 0.5,
      CLKOUT2_DUTY_CYCLE => 0.5,
      CLKOUT3_DUTY_CYCLE => 0.5,
      CLKOUT4_DUTY_CYCLE => 0.5,
      CLKOUT5_DUTY_CYCLE => 0.5,
      CLKOUT6_DUTY_CYCLE => 0.5,
      -- CLKOUT0_PHASE - CLKOUT6_PHASE: Phase offset for each CLKOUT (-360.000-360.000).
      CLKOUT0_PHASE => 0.0,
      CLKOUT1_PHASE => 0.0,
      CLKOUT2_PHASE => 0.0,
      CLKOUT3_PHASE => 0.0,
      CLKOUT4_PHASE => 0.0,
      CLKOUT5_PHASE => 0.0,
      CLKOUT6_PHASE => 0.0,
      CLKOUT4_CASCADE => FALSE,  -- Cascade CLKOUT4 counter with CLKOUT6 (FALSE, TRUE)
      REF_JITTER1 => 0.0,        -- Reference input jitter in UI (0.000-0.999).
      STARTUP_WAIT => FALSE      -- Delays DONE until MMCM is locked (FALSE, TRUE)
   )
   port map (
      -- Clock Outputs: 1-bit (each) output: User configurable clock outputs
      CLKOUT0   => open,     -- 1-bit output: CLKOUT0
      CLKOUT0B  => open,         -- 1-bit output: Inverted CLKOUT0
      CLKOUT1   => clk_pixel_x1, -- 1-bit output: CLKOUT1
      CLKOUT1B  => open,         -- 1-bit output: Inverted CLKOUT1
      CLKOUT2   => clk_pixel_x5, -- 1-bit output: CLKOUT2
      CLKOUT2B  => open,         -- 1-bit output: Inverted CLKOUT2
      CLKOUT3   => open,         -- 1-bit output: CLKOUT3
      CLKOUT3B  => open,         -- 1-bit output: Inverted CLKOUT3
      CLKOUT4   => open,         -- 1-bit output: CLKOUT4
      CLKOUT5   => open,         -- 1-bit output: CLKOUT5
      CLKOUT6   => open,         -- 1-bit output: CLKOUT6
      -- Feedback Clocks: 1-bit (each) output: Clock feedback ports
      CLKFBOUT  => clkfb,  -- 1-bit output: Feedback clock
      CLKFBOUTB => open,   -- 1-bit output: Inverted CLKFBOUT
      -- Status Ports: 1-bit (each) output: MMCM status ports
      LOCKED    => locked,   -- 1-bit output: LOCK
      -- Clock Inputs: 1-bit (each) input: Clock input
      CLKIN1    => clk100, -- 1-bit input: Clock
      -- Control Ports: 1-bit (each) input: MMCM control ports
      PWRDWN    => '0',    -- 1-bit input: Power-down
      RST       => '0',    -- 1-bit input: Reset
      -- Feedback Clocks: 1-bit (each) input: Clock feedback ports
      CLKFBIN   => clkfb   -- 1-bit input: Feedback clock
   );

i_vga_gen_1080p: vga_gen_1080p port map (
        clk        => clk_pixel_x1,
        blank      => blank,
        hsync      => hsync,
        vsync      => vsync
    );

count_process: process(    clk_pixel_x1)
    begin
        if rising_edge(clk_pixel_x1) then
            if blank = '1' then
                count <= (others => '0');
            else
                count <= std_logic_vector(unsigned(count)+1);
            end if;
        end if;
    end process;

i_vga_output: vga_output Port map (
            clk       => clk_pixel_x1,
            hsync_in  => hsync,
            vsync_in  => vsync,
            blank_in  => blank,
            count     => count,
            vga_hsync => vga_hsync,
            vga_vsync => vga_vsync,
            vga_red   => vga_red,
            vga_green => vga_green,
            vga_blue  => vga_blue,
            vga_blank => vga_blank
        );

 pixel_clk    <= clk_pixel_x1;
 pixel_clk_x5 <= clk_pixel_x5;

end Behavioral;