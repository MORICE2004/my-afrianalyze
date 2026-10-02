"""The Central Bank Rate loader finds the newest MPC statement and reads the decision. The two decision
sentences are quoted from the real statements (April and July 2026, bot.go.tz); the listing HTML is a
synthetic stand-in for the public notices page, and no network is used."""
from datetime import date

import pytest

import pipelines.macro as macro


@pytest.mark.parametrize("sentence,verb,rate", [
    # July 2026 statement, /Adverts/PressRelease/en/2026070313025546.pdf
    ("At its meeting held on 2 July 2026, the MPC raised the Central Bank Rate (CBR) from 5.75 percent to "
     "6.25 percent for the third quarter", "raised", "6.25"),
    # April 2026 statement, /Adverts/PressRelease/en/2026040215591446.pdf
    ("The MPC maintained the Central Bank Rate (CBR) at 5.75 percent for the quarter", "maintained", "5.75"),
    ("the Committee lowered the Central Bank Rate (CBR) from 6.25 percent to 6 percent", "lowered", "6"),
])
def test_the_decision_and_the_new_rate_are_read(sentence, verb, rate):
    m = macro.CBR_DECISION.search(sentence)
    assert m.group(1) == verb
    assert (m.group(3) or m.group(2)) == rate          # "to X" wins over "from Y"


def test_a_sentence_without_a_decision_gives_no_rate():
    m = macro.CBR_DECISION.search("The Central Bank Rate (CBR) is the policy rate of the Bank of Tanzania.")
    assert m is None


class _Page:
    status_code = 200

    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def test_the_newest_statement_is_chosen_and_the_calendar_is_ignored(monkeypatch):
    listing = """
      <a href="/Adverts/PressRelease/en/2026040215591446.pdf">Monetary Policy Committee Statement</a>
      <a href="/Adverts/PressRelease/en/2026070313025546.pdf">Monetary Policy Committee Statement</a>
      <a href="/Adverts/PressRelease/en/2026120111111111.pdf">MONETARY POLICY COMMITTEE (MPC) MEETINGS CALENDAR</a>
      <a href="/Adverts/PressRelease/en/2026080100000000.pdf">Treasury bills auction results</a>
    """
    monkeypatch.setattr(macro.requests, "get", lambda *a, **k: _Page(listing))
    url, published = macro.latest_mpc_statement()
    assert url == "https://www.bot.go.tz/Adverts/PressRelease/en/2026070313025546.pdf"
    assert published == date(2026, 7, 3)


def test_a_changed_page_layout_fails_instead_of_guessing(monkeypatch):
    monkeypatch.setattr(macro.requests, "get", lambda *a, **k: _Page("<html>nothing here</html>"))
    with pytest.raises(ValueError, match="No MPC statement listed"):
        macro.latest_mpc_statement()
