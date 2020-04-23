*** Settings ***
Suite Setup                   Setup
Suite Teardown                Teardown
Test Setup                    Reset Emulation
Resource                      ${RENODEKEYWORDS}

*** Test Cases ***
Print help and version
    [Documentation]           Runs Zephyr's shell sample and verifies if it is responsive

    # the path to the resc file is passed by the test-renode.sh script
    Execute Command           include @${LITEX_SCRIPT}

    Create Terminal Tester    sysbus.uart     timeout=240

    Start Emulation

    Wait For Prompt On Uart   uart:~$
    Write Line To Uart        help
    Wait For Line On Uart     Please refer to shell documentation for more details.

    Wait For Prompt On Uart   uart:~$
    Write Line To Uart        version
    Wait For Line On Uart     Zephyr version
    Wait For Prompt On Uart   uart:~$


