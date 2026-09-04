# Generator forensics

The prior semantic generator was located in the frozen commit, but it did not constitute the required formal runner: it lacked query-ID inputs, complete primary tracing, true lane-summed cost, and selection/holdout separation. A new formal runner and replay chain were therefore implemented and compared against the frozen positive signal.
