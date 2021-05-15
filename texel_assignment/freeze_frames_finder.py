# -*- coding: utf-8 -*-

import os
import logging
import textwrap
import subprocess

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO


class FreezeFrameFinderError(RuntimeError):
    pass


class FreezeFramesFinder:

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

    def aggregate(self, results):
        states = b'start', b'duration', b'end'
        current = 2
        by_url = {}
        interval = [None, None]

        for url, result in results:
            print(url)
            by_url[url] = intervals = []
            for line in BytesIO(result):
                if line.startswith(b'[freezedetect'):
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
                    # print(state, value)
        print(by_url)

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
            return self.aggregate(results)
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
