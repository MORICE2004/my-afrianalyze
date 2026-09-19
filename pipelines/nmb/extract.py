r"""NMB entry point kept for the documented commands. The pipeline lives in
pipelines/banks/extract.py and is shared by every bank.

    .venv\Scripts\python -m pipelines.nmb.extract
"""
import sys

from pipelines.banks.extract import main

if __name__ == "__main__":
    sys.exit(main(["--bank=nmb", *sys.argv[1:]]))
