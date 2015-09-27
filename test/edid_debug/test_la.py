from litescope.software.driver.logic_analyzer import LiteScopeLogicAnalyzerDriver


def main(wb):
    wb.open()
    # # #
    logic_analyzer = LiteScopeLogicAnalyzerDriver(wb.regs, "logic_analyzer", debug=True)

#    cond = {"hdmi_in0_edid_scl_raw" : 0}
    cond = {"hdmi_in0_edid_fsm_state" : 2}
#    cond = {}
    logic_analyzer.configure_term(port=0, cond=cond)
    logic_analyzer.configure_sum("term")
    logic_analyzer.configure_subsampler(64)
    logic_analyzer.run(offset=128, length=8192)

    while not logic_analyzer.done():
        pass
    logic_analyzer.upload()

    logic_analyzer.save("dump.vcd")
    # # #
    wb.close()
