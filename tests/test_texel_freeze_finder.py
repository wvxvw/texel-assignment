# -*- coding: utf-8 -*-

import os
from glob import glob

from texel_assignment.freeze_frames_finder import FreezeFramesFinder


def test_freeze_sync():
    finder = FreezeFramesFinder(None, None)
    intervals = {
        0: [(0, 1), (2, 3), (4, 5)],
        1: [(0, 1.5), (2.5, 3.5), (4.5, 5.5)],
        2: [(0, 1.2), (2.3, 3.1), (4.0, 5.5)],
    }
    assert finder.all_videos_freeze_frame_synced(intervals)


def test_valid_percentage():
    finder = FreezeFramesFinder(None, None)
    intervals = (0, 25), (50, 75), (100, 125)
    assert finder.valid_video_percentage(intervals) == 25 * 3 * 100 / 125
    

def test_longest_period():
    finder = FreezeFramesFinder(None, None)
    intervals = (0, 25), (50, 76), (100, 125)
    assert finder.longest_valid_period(intervals) == 26


def test_aggregate():
    finder = FreezeFramesFinder(None, None)
    data_dir = os.path.join(
        os.path.dirname(__file__),
        'data',
    )
    outputs = []
    for out in glob(os.path.join(data_dir, '*.out')):
        with open(out, 'rb') as o:
            outputs.append((out, o.read()))
    expected = {
        'ffmpeg.2.out': (
            (0.0, 4.5045),
            (10.6106, 12.0787),
            (14.4311, 18.018),
            (25.5755, 29.06),
        ),
        'ffmpeg.3.out': (
            (0.0, 4.5045),
            (8.3083, 9.97663),
            (12.1288, 16.016),
            (23.2733, 26.76),
        ),
        'ffmpeg.1.out': (
            (0.0, 4.5045),
            (10.4271, 12.012),
            (14.2476, 18.018),
            (25.392, 29.06),
        )
    }
    actual = {
        os.path.basename(k): v
        for k, v in finder.aggregate(outputs).items()
    }
    assert actual == expected


def test_invert_intervals():
    finder = FreezeFramesFinder(None, None)
    intervals = list(zip(range(1, 10), range(2, 11)))
    expected = tuple([(0.0, 1)] + [(i, i) for i in range(2, 10)] + [(10, 11)])
    assert finder.invert_intervals(intervals, 11) == expected
