import DAXI_template_eSPIM

test_obj = DAXI_template_eSPIM.NIDaq(exposure=10, nb_timepoints=5, scan_step=2.5, stage_scan_range=2.5)

print(test_obj._get_do_data([1]))