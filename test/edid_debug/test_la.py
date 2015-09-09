from litescope.software.driver.la import LiteScopeLADriver


def main(wb):
    wb.open()
    # # #
    la = LiteScopeLADriver(wb.regs, "la", debug=True)

#    cond = {"hdmi_in0_edid_scl_raw" : 0}
    cond = {"hdmi_in0_edid_fsm_state" : 2}
#    cond = {}
    la.configure_term(port=0, cond=cond)
    la.configure_sum("term")
    la.configure_subsampler(64)
    la.run(offset=128, length=8192)

    while not la.done():
        pass
    la.upload()

    la.save("dump.vcd")
    # # #
    wb.close()
