control_tokens = [
    # Control tokens are designed to have a large number (7) of transitions to
    # help the receiver synchronize its clock with the transmitter clock.
    # Control tokens are encoded using the values in the table below.
    # 9........0     C1  C0
    0b1101010100,  #  0   0
    0b0010101011,  #  0   1
    0b0101010100,  #  1   0
    0b1010101011,  #  1   1
]

channel_layout = [("d", 8), ("c", 2), ("de", 1)]
