*** Settings ***
Suite Setup                  Setup
Suite Teardown               Teardown
Test Setup                   Reset Emulation
Resource                     ${RENODEKEYWORDS}

*** Test Cases ***
Print help
    [Documentation]          Runs HDMI2USB Firmware and verifies if the user interface is responsive

    # the path to the resc file is passed by the test-renode.sh script
    Execute Command          include @${LITEX_SCRIPT}

    Create Terminal Tester   sysbus.uart  timeout=120

    Start Emulation

    Wait For Line On Uart    HDMI2USB firmware booting...
    Wait For Prompt On Uart  H2U${SPACE}

    Write line To Uart       help
    Wait For Line On Uart    Available commands:
    Wait For Line On Uart    status commands
    Wait For Line On Uart    video_matrix commands
    Wait For Line On Uart    video_mode commands
    Wait For Line On Uart    change heartbeat status
    Wait For Line On Uart    debug commands

