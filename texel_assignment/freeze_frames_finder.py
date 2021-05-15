# -*- coding: utf-8 -*-

import json
import logging
import os
import re
import subprocess
import sys
import textwrap

from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from io import BytesIO


class FreezeFrameFinderError(RuntimeError):
    pass


class FreezeFramesFinder:

    freezedetect_noise = 0.003

    sync_tolerance = 0.5

    duration_re = re.compile(
        br'(?P<hours>\d\d):(?P<minutes>\d\d):(?P<seconds>\d\d\.\d\d)'
    )

    def __init__(self, output, urls):
        self.output = output
        self.urls = urls

    def process_url(self, url):
        try:
            return subprocess.check_output(
                [
                    'ffmpeg',
                    '-hide_banner',
                    '-nostats',
                    '-i', url,
                    '-vf', 'freezedetect=n={:.03}'.format(
                        self.freezedetect_noise,
                    ),
                    '-f', 'null',
                    '-',
                ],
                stderr=subprocess.STDOUT,
            ), True
        except subprocess.CalledProcessError as e:
            return e.output, False

    def parse_duration(self, raw):
        match = re.match(self.duration_re, raw)
        return (
            int(match.group('hours')) * 60 * 60 +
            int(match.group('minutes')) * 60 +
            float(match.group('seconds'))
        )

    def invert_intervals(self, intervals, duration):
        result = [0.0] + sum(
            (list(pair) for pair in intervals),
            start=[],
        ) + [duration]
        return tuple(
            (start, end)
            for start, end in zip(result, result[1:])
        )[::2]

    def aggregate(self, results):
        states = b'start', b'duration', b'end'
        current = 2
        by_url = {}
        durations = {}
        interval = [None, None]

        for url, result in results:
            by_url[url] = intervals = []
            for line in BytesIO(result):
                if line.startswith(b'  Duration: '):
                    _, duration, _ = line.split(maxsplit=2)
                    durations[url] = self.parse_duration(duration)
                elif line.startswith(b'[freezedetect'):
                    prefix, suffix = line.split(b': ')
                    current = (current + 1) % len(states)
                    state = states[current]
                    value = float(suffix.strip())
                    if not prefix.endswith(state):
                        logging.warning(
                            'Failed to parse some output. '
                            'Expected {}, found {}'.format(
                                state,
                                line,
                            ))
                        break
                    if state == b'start':
                        interval[0] = value
                    elif state == b'end':
                        interval[1] = value
                        intervals.append(tuple(interval))
        inverted = {}
        for url, intervals in by_url.items():
            inverted[url] = self.invert_intervals(intervals, durations[url])
        return inverted

    def longest_valid_period(self, intervals):
        start, end = max(intervals, key=lambda i: i[1] - i[0])
        return end - start

    def valid_video_percentage(self, intervals):
        duration = intervals[-1][-1]
        return (100 * sum(i[1] - i[0] for i in intervals)) / duration

    def report_video(self, intervals):
        return {
            'longest_valid_period': self.longest_valid_period(intervals),
            'valid_video_percentage': self.valid_video_percentage(intervals),
            'valid_periods': intervals,
        }

    def compute_extremi(self, *args):
        return max(args), min(args)

    def all_videos_freeze_frame_synced(self, aggregated):
        lengths = tuple(len(intervals) for intervals in aggregated.values())
        if not all(a == b for a, b in zip(lengths, lengths[:1])):
            return False
        flat = (
            reduce(lambda a, b: a + list(b), pairs, [])
            for pairs in aggregated.values()
        )
        extremi = map(self.compute_extremi, *flat)
        return all(
            maxv - minv <= self.sync_tolerance for maxv, minv in extremi
        )

    def format_output(self, aggregated):
        report = {
            'all_videos_freeze_frame_synced':
            self.all_videos_freeze_frame_synced(
                aggregated,
            ),
            'videos': [
                self.report_video(intervals)
                for intervals in aggregated.values()
            ]
        }
        if not self.output:
            json.dump(report, sys.stdout, indent=4)
        else:
            with open(self.output, 'w') as f:
                json.dump(report, f, indent=4)

    def run(self):
        failures, results = [], []
        with ThreadPoolExecutor(len(os.sched_getaffinity(0)) - 1) as executor:
            for url, (pout, success) in zip(
                    self.urls,
                    executor.map(self.process_url, self.urls),
            ):
                if success:
                    results.append((url, pout))
                else:
                    failures.append((url, pout))

        if not failures:
            aggregated = self.aggregate(results)
            return self.format_output(aggregated)
        elif results and failures:
            logging.warning('Some videos failed filtering:')
            for url, f in failures:
                logging.warning('{}: {}'.format(url, f))
        else:
            raise FreezeFrameFinderError(textwrap.dedent(
                '''
                Failed to process URLs:
                {}
                ''',
            ).format(
                ':\n'.join([
                    url,
                    textwrap.indent(f, prefix='  ')
                ]) for f in failures
            ))
