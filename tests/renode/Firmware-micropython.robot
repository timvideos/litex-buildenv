*** Settings ***
Suite Setup                   Setup
Suite Teardown                Teardown
Test Setup                    Reset Emulation
Resource                      ${RENODEKEYWORDS}

*** Test Cases ***
Print help and version
    [Documentation]           Runs Micropython REPL and verifies if it is responsive

    # the path to the resc file is passed by the test-renode.sh script
    Execute Command           include @${LITEX_SCRIPT}

    Create Terminal Tester    sysbus.uart  timeout=120

    Start Emulation

    Wait For Line On Uart     MicroPython
    Wait For Prompt On Uart   >>>

    Write Line To Uart        2 + 3
    Wait For Line On Uart     5
    Wait For Prompt On Uart   >>> 

