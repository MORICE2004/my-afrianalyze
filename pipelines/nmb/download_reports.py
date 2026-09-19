r"""NMB entry point kept for the documented commands. The pipeline lives in
pipelines/banks/download_reports.py and is shared by every bank.

    .venv\Scripts\python -m pipelines.nmb.download_reports
"""
import sys

from pipelines.banks.download_reports import main

if __name__ == "__main__":
    sys.exit(main(["--bank=nmb", *sys.argv[1:]]))
