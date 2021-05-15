# -*- coding: utf-8 -*-

from argparse import ArgumentParser


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
    'url',
    help='''
    List of URLs to videos we need to process.
    ''',
    nargs='+',
)


def main(cli_args):
    pargs = parser.parse_args(cli_args)
    return 0
