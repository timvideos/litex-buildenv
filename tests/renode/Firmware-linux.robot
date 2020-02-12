*** Settings ***
Suite Setup                   Setup
Suite Teardown                Teardown
Test Setup                    Reset Emulation
Resource                      ${RENODEKEYWORDS}

*** Test Cases ***
Boot
    [Documentation]           Runs Linux and verifies that the shell is responsive

    # the path to the resc file is passed by the test-renode.sh script
    Execute Command           include @${LITEX_SCRIPT}

    Create Terminal Tester    sysbus.uart    timeout=120

    Start Emulation

    Wait For Line On Uart     Linux version 5.0.0
    Wait For Line On Uart     Welcome to Buildroot

    Wait For Prompt On Uart   buildroot login:
    Write Line To Uart        root

    Wait For Line On Uart     login[48]: root login on 'hvc0'
    Wait For Prompt On Uart   \#

    Write Line To Uart        ls /
    Wait For Line On Uart     etc

