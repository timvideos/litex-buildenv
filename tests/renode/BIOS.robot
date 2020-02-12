*** Settings ***
Suite Setup                  Setup
Suite Teardown               Teardown
Test Setup                   Reset Emulation
Resource                     ${RENODEKEYWORDS}

*** Test Cases ***
BIOS boots
    [Documentation]          Runs LiteX BIOS and verifies if the configuration info is printed on UART

    # the path to the resc file is passed by the test-renode.sh script
    Execute Command          include @${LITEX_SCRIPT}

    Create Terminal Tester   sysbus.uart  timeout=120

    Start Emulation

    Wait For Line On Uart    BIOS built on
    Wait For Line On Uart    BIOS CRC passed

    # CPU_TYPE variable is passed by the test-renode.sh script
    Wait For Line On Uart    CPU:\\s* ${CPU_TYPE} @ [0-9]+MHz       treatAsRegex=true

