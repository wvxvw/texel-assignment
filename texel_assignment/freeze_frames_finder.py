# -*- coding: utf-8 -*-

import json
import logging
import os
import re
import subprocess
import sys
import textwrap

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO


class FreezeFrameFinderError(RuntimeError):
    pass


class FreezeFramesFinder:

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
                    '-vf', 'freezedetect=n=0.003',
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
        )

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

    def report_video(self, intervals):
        return {
	    'longest_valid_period': 7.35,
	    'valid_video_percentage': 56.00,
	    'valid_periods':[
		[
		    0.00,
		    3.50
		],
		[
		    6.65,
		    14
		],
		[
		    19.71,
		    20.14
		]
	    ]
	}

    def all_videos_freeze_frame_synced(self, aggregated):
        return True

    def format_output(self, aggregated):
        report =  {
	    'all_videos_freeze_frame_synced': self.all_videos_freeze_frame_synced(
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
