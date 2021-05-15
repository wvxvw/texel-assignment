#!/bin/sh

set -ex

texel-detect-frozen \
    https://storage.googleapis.com/hiring_process_data/freeze_frame_input_a.mp4 \
    https://storage.googleapis.com/hiring_process_data/freeze_frame_input_b.mp4 \
    https://storage.googleapis.com/hiring_process_data/freeze_frame_input_c.mp4
