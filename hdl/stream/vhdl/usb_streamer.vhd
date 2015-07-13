-- Copyright (c) 2013, Jahanzeb Ahmad
-- Copyright (c) 2015, Florent Kermarrec

library IEEE;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;

entity usb_streamer is
  port
    (
      -- Clock / Reset
      rst : in std_logic;
      clk : in std_logic;

      -- Sink
      sink_stb  : in  std_logic;
      sink_ack  : out std_logic;
      sink_data : in  std_logic_vector(7 downto 0);

      -- Cypress FX2 slave fifo interface
      ifclk      : in    std_logic;
      fdata      : inout std_logic_vector(7 downto 0);
      flag_full  : in    std_logic;
      flag_empty : in    std_logic;
      faddr      : out   std_logic_vector(1 downto 0);
      slcs       : out   std_logic;
      slwr       : out   std_logic;
      slrd       : out   std_logic;
      sloe       : out   std_logic;
      pktend     : out   std_logic
      );
end entity usb_streamer;

architecture rtl of usb_streamer is

  signal jpeg_rd_en      : std_logic;
  signal jpeg_fifo_empty : std_logic;
  signal pkt_sent        : std_logic;
  signal fid             : std_logic;

  signal sink_data_d : std_logic_vector(7 downto 0);

  signal wrightcount : std_logic_vector(11 downto 0);

  type fsm_states is (uvc_wait,
                      uvc_in_pktend,
                      uvc_send_data,
                      s_reset,
                      free_uvc,
                      s_skip);
  signal fsm_state : fsm_states;

  signal prog_full : std_logic;

begin

  slcs  <= '0';
  sloe  <= '1';
  slrd  <= '1';
  faddr <= "10";

  syncProc : process(rst, ifclk)
  begin

    if rst = '1' then
      slwr        <= '1';
      pktend      <= '1';
      fid         <= '0';
      pkt_sent    <= '0';
      wrightcount <= (others => '0');
      sink_data_d <= (others => '0');
      fsm_state   <= s_reset;
    elsif falling_edge(ifclk) then

      slwr   <= '1';
      pktend <= '1';

      case fsm_state is
        when s_reset =>
          slwr        <= '1';
          pktend      <= '1';
          fid         <= '0';
          pkt_sent    <= '0';
          fsm_state   <= uvc_wait;
          fdata       <= (others => '0');
          sink_data_d <= (others => '0');
          wrightcount <= (others => '0');

        when uvc_send_data =>

          if sink_stb = '1' and flag_full = '1' then

            wrightcount <= wrightcount + 1;

            if wrightcount = X"400" then
              fsm_state   <= uvc_wait;
              wrightcount <= (others => '0');
            elsif wrightcount = X"000" then
              slwr     <= '0';
              fdata    <= X"0C";        -- header length
              pkt_sent <= '0';

            elsif wrightcount = X"001" then
              slwr  <= '0';
              fdata <= ("100" & "000" & "0" & fid);  -- EOH  ERR  STI  RES  SCR  PTS  EOF  FID

            elsif wrightcount <= X"00B" then
              slwr  <= '0';
              fdata <= X"00";

            else
              slwr        <= '0';
              sink_data_d <= sink_data;
              fdata       <= sink_data;
              if sink_data_d = X"FF" and sink_data = X"D9" then
                fid         <= not fid;
                fsm_state   <= uvc_in_pktend;
                pkt_sent    <= '1';
                wrightcount <= (others => '0');
              end if;

            end if;
          end if;

        when uvc_wait =>
          if flag_full = '1' then
            fsm_state <= uvc_send_data;
          end if;

        when uvc_in_pktend =>
          pktend    <= '0';
          fsm_state <= uvc_wait;

        when others =>
          fsm_state <= s_reset;
      end case;

    end if;

  end process;

  sink_ack <= (sink_stb and flag_full) when ((fsm_state = uvc_send_data) and (wrightcount > X"00B" and wrightcount < X"400")) else '0';

end architecture;
