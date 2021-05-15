# -*- coding: utf-8 -*-

import logging

from argparse import ArgumentParser

from .freeze_frames_finder import FreezeFramesFinder


parser = ArgumentParser('Find frozen frames in videos using ffmpeg')
parser.add_argument(
    '-o',
    '--output',
    help='''
    Specify a file to write output to (default is to output to stdout).
    ''',
    default=None,
)
parser.add_argument(
    'urls',
    help='''
    List of URLs to videos we need to process.
    ''',
    nargs='+',
)


def main(cli_args):
    pargs = parser.parse_args(cli_args)
    finder = FreezeFramesFinder(pargs.output, pargs.urls)
    try:
        finder.run()
    except Exception as e:
        logging.exception(e)
        return 1
    return 0
