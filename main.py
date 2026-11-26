#!/usr/bin/env python3
"""news-image-20261126: write one image summing up the world news of
Thursday 26 November 2026 to /output/entry.png.

The image is a newspaper front page generated for this entry: masthead
"THE WORLD", dateline "THURSDAY, 26 NOVEMBER 2026", six illustrated
panels for the day's biggest stories, and a footer strip on the 100th
Macy's Thanksgiving Day Parade postponed by a storm.

Pure standard library. Deterministic: the program copies the image the
repository holds, byte for byte, so two runs write identical output.
"""

import os
import shutil

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    dst = os.path.join(out_dir, "entry.png")
    with open(src, "rb") as f:
        head = f.read(len(PNG_SIGNATURE))
    if head != PNG_SIGNATURE:
        raise ValueError("entry.png is not a PNG file")
    shutil.copyfile(src, dst)
    if os.path.getsize(dst) != os.path.getsize(src):
        raise ValueError("copied entry.png does not match the source")


if __name__ == "__main__":
    main()
