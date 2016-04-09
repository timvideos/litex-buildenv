-------------------------------------------------------------------------------
--
-- Copyright (c) 2013, Jahanzeb Ahmad
-- Copyright (c) 2015, Florent Kermarrec
--
-- fx2_jpeg_streamer
--
-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
-- L I B R A R I E S
-------------------------------------------------------------------------------
library IEEE;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-------------------------------------------------------------------------------
-- E N T I T Y
-------------------------------------------------------------------------------
entity fx2_jpeg_streamer is
  port
    (
      -- Clock / Reset
    ---------------------------------------------------------------------------
      rst : in std_logic;
      clk : in std_logic;

      -- Sink
    ---------------------------------------------------------------------------
      sink_stb  : in  std_logic;
      sink_ack  : out std_logic;
      sink_data : in  std_logic_vector(7 downto 0);

      -- FX2 slave fifo interface
      ---------------------------------------------------------------------------
      fx2_data     : inout std_logic_vector(7 downto 0);
      fx2_full_n   : in    std_logic;
      fx2_empty_n  : in    std_logic;
      fx2_addr     : out   std_logic_vector(1 downto 0);
      fx2_cs_n     : out   std_logic;
      fx2_wr_n     : out   std_logic;
      fx2_rd_n     : out   std_logic;
      fx2_oe_n     : out   std_logic;
      fx2_pktend_n : out   std_logic
      );
end entity fx2_jpeg_streamer;

-------------------------------------------------------------------------------
-- A R C H I T E C T U R E
-------------------------------------------------------------------------------
architecture rtl of fx2_jpeg_streamer is

  --===================================--
  -- Signals Declaration
  --===================================--
  signal packet_sent    : std_logic;
  signal packet_fid     : std_logic;
  signal packet_counter : unsigned(11 downto 0);

  signal sink_data_d : std_logic_vector(7 downto 0);

  type fsm_states is (S_RESET,
  	                  S_WAIT,
                      S_PACKET_END,
                      S_SEND_DATA);
  signal fsm_state : fsm_states;

  signal sending_data : std_logic;

begin

  --===========================================================================
  -- Static assignements
  --===========================================================================
  fx2_cs_n  <= '0';
  fx2_oe_n  <= '1';
  fx2_rd_n  <= '1';
  fx2_addr  <= "10";

  --===========================================================================
  -- Main process
  --===========================================================================
  main_p : process(rst, clk)
  begin

    if rst = '1' then
      fx2_wr_n       <= '1';
      fx2_pktend_n   <= '1';
      packet_fid     <= '0';
      packet_sent    <= '0';
      packet_counter <= (others => '0');
      sink_data_d    <= (others => '0');
      fsm_state      <= S_RESET;
    elsif falling_edge(clk) then

      fx2_wr_n     <= '1';
      fx2_pktend_n <= '1';

      case fsm_state is

        when S_RESET =>
          packet_fid     <= '0';
          packet_sent    <= '0';
          fsm_state      <= S_WAIT;
          fx2_data       <= (others => '0');
          sink_data_d    <= (others => '0');
          packet_counter <= (others => '0');

        when S_WAIT =>
          if fx2_full_n = '1' then
            fsm_state <= S_SEND_DATA;
          end if;

        when S_SEND_DATA =>

          if sink_stb = '1' and fx2_full_n = '1' then

            packet_counter <= packet_counter + 1;

            if packet_counter = 1024 then
              fsm_state   <= S_WAIT;
              packet_counter <= (others => '0');
            elsif packet_counter = 0 then
              fx2_wr_n    <= '0';
              fx2_data    <= X"0C"; -- header length
              packet_sent <= '0';

            elsif packet_counter = 1 then
              fx2_wr_n  <= '0';
              -- EOH  ERR  STI  RES  SCR  PTS  EOF  packet_fid
              fx2_data <= ("100" & "000" & "0" & packet_fid);

            elsif packet_counter <= 11 then
              fx2_wr_n <= '0';
              fx2_data <= X"00";

            else
              fx2_wr_n    <= '0';
              sink_data_d <= sink_data;
              fx2_data    <= sink_data;
              if sink_data_d = X"FF" and sink_data = X"D9" then
                packet_fid     <= not packet_fid;
                fsm_state      <= S_PACKET_END;
                packet_sent    <= '1';
                packet_counter <= (others => '0');
              end if;

            end if;
          end if;

        when S_PACKET_END =>
          fx2_pktend_n  <= '0';
          fsm_state     <= S_WAIT;

        when others =>
          fsm_state <= S_RESET;
      end case;

    end if;

  end process;

  sending_data <= '1' when ((fsm_state = S_SEND_DATA) and (packet_counter > X"00B" and packet_counter < X"400")) else
  	              '0';
  sink_ack <= (sink_stb and fx2_full_n) when sending_data = '1' else '0';

end architecture;
