"""Rotate log files in a directory."""

import argparse
import glob
import os


def rotate(directory, keep):
    if keep < 1:
        raise ValueError("keep must be at least 1")
    files = sorted(glob.glob(os.path.join(directory, "*.log")))
    for index, path in enumerate(files):
        os.replace(path, f"{path}.{index + 1}")
    return files


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    parser.add_argument("--keep", type=int, default=7)
    args = parser.parse_args(argv)
    rotate(args.directory, args.keep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
