r"""NMB entry point kept for the documented commands. The pipeline lives in
pipelines/banks/resolve.py and is shared by every bank.

    .venv\Scripts\python -m pipelines.nmb.resolve
"""
import sys

from pipelines.banks.resolve import main

if __name__ == "__main__":
    sys.exit(main(["--bank=nmb", *sys.argv[1:]]))
