-- //////////////////////////////////////////////////////////////////////////////
-- /// Copyright (c) 2013, Jahanzeb Ahmad
-- /// All rights reserved.
-- ///
-- // Redistribution and use in source and binary forms, with or without modification,
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

LIBRARY IEEE;
USE ieee.std_logic_1164.all;
USE ieee.std_logic_arith.all;
USE ieee.std_logic_unsigned.all;

entity usb_streamer is
  port
  (
	-- jpeg encoder
	jpeg_byte	: in std_logic_vector(7 downto 0);
	jpeg_clk 	: in std_logic;
	jpeg_en		: in std_logic;
	jpeg_fifo_full : out std_logic;

	-- cypress chip signals
	fdata		: inout std_logic_vector(7 downto 0);
	flag_full 	: in std_logic;
	flag_empty 	: in std_logic;
	faddr		: out std_logic_vector(1 downto 0);
	slwr		: out std_logic;
	slrd		: out std_logic;
	sloe		: out std_logic;
	pktend		: out std_logic;
	ifclk		: in std_logic;

	-- clk,rst
	rst 		: in std_logic;
	clk 		: in std_logic
  );
end entity usb_streamer;

architecture rtl of usb_streamer is


----------- signals
signal slwr_jpg_uvc : std_logic;
signal pktend_jpg_uvc : std_logic;
signal fdataout : std_logic_vector(7 downto 0);
signal fdataout_jpg_uvc : std_logic_vector(7 downto 0);

-- components signals

begin  -- architecture
sloe 			<= '1';
faddr 			<= "10";

fdata <= fdataout;

syncProc: process(rst,ifclk) -- usb process
begin -- process

if rst = '1' then
	slwr		<= '1';
	slrd		<= '1';
	pktend		<= '1';
	fdataout    <= (others => '0');
elsif falling_edge(ifclk) then
	slrd		<= '1';
	slwr		<= slwr_jpg_uvc;
	pktend		<= pktend_jpg_uvc;
	fdataout	<= fdataout_jpg_uvc;
end if;

end process;

---------------------- components
jpg_uvc_comp: entity work.jpg_uvc
	port map(jpeg_en        => jpeg_en,
		     jpeg_byte      => jpeg_byte,
		     jpeg_fifo_full => jpeg_fifo_full,
		     jpeg_clk       => jpeg_clk,
		     slwr           => slwr_jpg_uvc,
		     pktend         => pktend_jpg_uvc,
		     fdata          => fdataout_jpg_uvc,
		     flag_full      => flag_full,
		     ifclk          => ifclk,
		     uvc_rst        => rst);

end architecture;
