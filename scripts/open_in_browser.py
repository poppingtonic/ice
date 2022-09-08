#! /usr/bin/env python
import re
import sys

from subprocess import run


def open_in_browser(url):
    try:
        run(["open", url])
    except FileNotFoundError:
        try:
            run(["xdg-open", url])
        except FileNotFoundError:
            # Unable to open browser: do nothing.
            pass


opening_pattern = re.compile(r"Opening trace: (http.*)")


def main():
    for line in sys.stdin:
        if m := opening_pattern.match(line):
            open_in_browser(m.group(1))
        sys.stdout.write(line)


if __name__ == "__main__":
    main()
