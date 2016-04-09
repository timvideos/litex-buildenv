-------------------------------------------------------------------------------
-- File Name : HostIF.vhd
--
-- Project   : JPEG_ENC
--
-- Module    : HostIF
--
-- Content   : Host Interface (Xilinx OPB v2.1)
--
-- Description :
--
-- Spec.     :
--
-- Author    : Michal Krepa
--
-------------------------------------------------------------------------------
-- History :
-- 20090301: (MK): Initial Creation.
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
  use ieee.numeric_std.all;

entity HostIF is
  port
  (
        CLK                : in  std_logic;
        RST                : in  std_logic;
        -- OPB
        OPB_ABus           : in  std_logic_vector(11 downto 0);
        OPB_BE             : in  std_logic_vector(3 downto 0);
        OPB_DBus_in        : in  std_logic_vector(31 downto 0);
        OPB_RNW            : in  std_logic;
        OPB_select         : in  std_logic;
        OPB_DBus_out       : out std_logic_vector(31 downto 0);
        OPB_XferAck        : out std_logic;
        OPB_retry          : out std_logic;
        OPB_toutSup        : out std_logic;
        OPB_errAck         : out std_logic;

        -- Quantizer RAM
        qdata              : out std_logic_vector(7 downto 0);
        qaddr              : out std_logic_vector(6 downto 0);
        qwren              : out std_logic;

        -- CTRL
        jpeg_ready         : in  std_logic;
        jpeg_busy          : in  std_logic;

        -- ByteStuffer
        outram_base_addr   : out std_logic_vector(9 downto 0);
        num_enc_bytes      : in  std_logic_vector(23 downto 0);

        -- others
        img_size_x         : out std_logic_vector(15 downto 0);
        img_size_y         : out std_logic_vector(15 downto 0);
        img_size_wr        : out std_logic;
        sof                : out std_logic

    );
end entity HostIF;

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
----------------------------------- ARCHITECTURE ------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
architecture RTL of HostIF is

  constant C_ENC_START_REG          : std_logic_vector(11 downto 0) := X"000";
  constant C_IMAGE_SIZE_REG         : std_logic_vector(11 downto 0) := X"004";
  constant C_IMAGE_RAM_ACCESS_REG   : std_logic_vector(11 downto 0) := X"008";
  constant C_ENC_STS_REG            : std_logic_vector(11 downto 0) := X"00C";
  constant C_COD_DATA_ADDR_REG      : std_logic_vector(11 downto 0) := X"010";
  constant C_ENC_LENGTH_REG         : std_logic_vector(11 downto 0) := X"014";
  constant C_QUANTIZER_RAM_LUM_BASE : std_logic_vector(11 downto 0) := X"100";
  constant C_QUANTIZER_RAM_CHR_BASE : std_logic_vector(11 downto 0) := X"200";

  signal enc_start_reg            : std_logic_vector(31 downto 0);
  signal image_size_reg           : std_logic_vector(31 downto 0);
  signal image_ram_access_reg     : std_logic_vector(31 downto 0);
  signal enc_sts_reg              : std_logic_vector(31 downto 0);
  signal cod_data_addr_reg        : std_logic_vector(31 downto 0);

  signal read_ack                : std_logic;
  signal write_ack               : std_logic;

-------------------------------------------------------------------------------
-- Architecture: begin
-------------------------------------------------------------------------------
begin

  OPB_retry    <= '0';
  OPB_toutSup  <= '0';
  OPB_errAck   <= '0';

  img_size_x <= image_size_reg(31 downto 16);
  img_size_y <= image_size_reg(15 downto 0);

  outram_base_addr <= cod_data_addr_reg(outram_base_addr'range);

  -------------------------------------------------------------------
  -- OPB read
  -------------------------------------------------------------------
  p_read : process(CLK, RST)
  begin
    if RST = '1' then
      read_ack       <= '0';
      OPB_DBus_out    <= (others => '0');
    elsif CLK'event and CLK = '1' then
      read_ack <= '0';
      if OPB_select = '1' and read_ack = '0' then
        -- only double word transactions are be supported
        if OPB_RNW = '1' and OPB_BE = X"F" then
          read_ack <= '1';
          case OPB_ABus is
            when C_ENC_START_REG =>
              OPB_DBus_out <= enc_start_reg;
            when C_IMAGE_SIZE_REG =>
              OPB_DBus_out <= image_size_reg;
            when C_IMAGE_RAM_ACCESS_REG =>
              OPB_DBus_out <= image_ram_access_reg;
            when C_ENC_STS_REG =>
              OPB_DBus_out <= enc_sts_reg;
            when C_COD_DATA_ADDR_REG =>
              OPB_DBus_out <= cod_data_addr_reg;
            when C_ENC_LENGTH_REG =>
              OPB_DBus_out(31 downto 24) <= (others => '0');
              OPB_DBus_out(23 downto 0)  <= num_enc_bytes;
            when others =>
              OPB_DBus_out <= (others => '0');
          end case;
        end if;
      end if;
    end if;
  end process;

  -------------------------------------------------------------------
  -- OPB write
  -------------------------------------------------------------------
  p_write : process(CLK, RST)
  begin
    if RST = '1' then
      qwren                <= '0';
      write_ack           <= '0';
      enc_start_reg        <= (others => '0');
      image_size_reg       <= (others => '0');
      image_ram_access_reg <= (others => '0');
      enc_sts_reg          <= (others => '0');
      cod_data_addr_reg    <= (others => '0');
      qdata                <= (others => '0');
      qaddr                <= (others => '0');
      sof                  <= '0';
      img_size_wr          <= '0';
    elsif CLK'event and CLK = '1' then
      qwren       <= '0';
      write_ack   <= '0';
      sof         <= '0';
      img_size_wr <= '0';

      if OPB_select = '1' and write_ack = '0' then
        -- only double word transactions are be supported
        if OPB_RNW = '0' and OPB_BE = X"F" then
          write_ack <= '1';
          case OPB_ABus is
            when C_ENC_START_REG =>
              enc_start_reg <= OPB_DBus_in;
              if OPB_DBus_in(0) = '1' then
                sof <= '1';
              end if;

            when C_IMAGE_SIZE_REG =>
              image_size_reg <= OPB_DBus_in;
              img_size_wr <= '1';

            when C_IMAGE_RAM_ACCESS_REG =>
              image_ram_access_reg <= OPB_DBus_in;

            when C_ENC_STS_REG =>
              enc_sts_reg <= (others => '0');

            when C_COD_DATA_ADDR_REG =>
              cod_data_addr_reg <= OPB_DBus_in;

            when C_ENC_LENGTH_REG =>
              --enc_length_reg <= OPB_DBus_in;

            when others =>
              if OPB_ABus(11 downto 8) = C_QUANTIZER_RAM_LUM_BASE(11 downto 8) then
                qwren      <= '1';
                qaddr      <= '0' & OPB_ABus(qaddr'high+2-1 downto 2);
              elsif OPB_ABus(11 downto 8) = C_QUANTIZER_RAM_CHR_BASE(11 downto 8) then
                qwren      <= '1';
                qaddr      <= '1' & OPB_ABus(qaddr'high+2-1 downto 2);
              end if;
          end case;

        end if;

        qdata      <= OPB_DBus_in(qdata'range);

      end if;

      -- special handling of status reg
      if jpeg_ready = '1' then
        -- set jpeg done flag
        enc_sts_reg(1) <= '1';
      end if;
      enc_sts_reg(0) <= jpeg_busy;

    end if;
  end process;

  -------------------------------------------------------------------
  -- transfer ACK
  -------------------------------------------------------------------
  OPB_XferAck <= read_ack or write_ack;

end architecture RTL;
-------------------------------------------------------------------------------
-- Architecture: end
-------------------------------------------------------------------------------