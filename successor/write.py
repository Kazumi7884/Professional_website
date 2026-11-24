"""Open the existing local writing desk against the current static site."""
import argparse
import sys
import time

from build import ROOT, SUBJECT_GROUPS, build

# Reuse the existing authoring server and its localhost/security boundaries.
sys.path.insert(0, str(ROOT / 'tools'))
from studio import serve


def build_for_desk():
    start = time.monotonic()
    report = build()
    return {'pages': report['canonical_routes'], 'seconds': round(time.monotonic() - start, 3)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    serve(args.port, build_for_desk, ROOT / 'build', SUBJECT_GROUPS)
