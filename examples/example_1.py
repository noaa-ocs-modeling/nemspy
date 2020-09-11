#! /usr/bin/env python
import sys
import pathlib
sys.path.insert(0, str((pathlib.Path(__file__).parent / '..').resolve()))

from NEMSpy.nems import NEMS  # noqa: E402


def main():
    nems = NEMS()


if __name__ == '__main__':
    main()
