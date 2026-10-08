"""Economic news: feed parsing, rule-based relevance, caching and the API. The parser inputs are trimmed copies
of each publisher's real structure (the Central Bank of Kenya RSS feed, the Bank of Tanzania press-release table
and the World Bank news API as fetched on 2026-10-08); no network is used."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import apps.api.main as api
from packages.database.models import DataSourceStatus, NewsItem
from packages.news.classify import classify
from pipelines import news
from tests.v1.test_auth_and_portfolios import db  # noqa: F401  (fixture)

SECURITIES = [
    {"id": "DSE:NMB", "name": "NMB Bank Plc", "ticker": "NMB", "exchange": "DSE", "sector": "Banking", "country_code": "TZ"},
    {"id": "DSE:CRDB", "name": "CRDB Bank Plc", "ticker": "CRDB", "exchange": "DSE", "sector": "Banking", "country_code": "TZ"},
    {"id": "DSE:TBL", "name": "Tanzania Breweries Limited", "ticker": "TBL", "exchange": "DSE", "sector": "Manufacturing", "country_code": "TZ"},
    {"id": "NSE:EQTY", "name": "Equity Group Holdings Plc", "ticker": "EQTY", "exchange": "NSE", "sector": "Banking", "country_code": "KE"},
]

RSS = b"""<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>CBK</title>
<item><title>MPC retains the CBR at 8.75 percent</title>
<link>https://www.centralbank.go.ke/2026/10/07/mpc-retains-the-cbr-at-8-75-percent-3/</link>
<pubDate>Wed, 07 Oct 2026 16:03:48 +0000</pubDate><description><![CDATA[<p>The MPC met...</p>]]></description></item>
<item><title>CEOs Survey of July 2026</title><link>https://www.centralbank.go.ke/2026/08/24/ceos-survey/</link>
<pubDate>Mon, 24 Aug 2026 09:00:00 +0000</pubDate></item>
</channel></rss>"""

BOT = b"""<table><tr><th>Na.</th><th>Title</th><th>Date</th></tr>
<tr><td>1.</td><td><a href="/Adverts/PressRelease/en/2026100815530593.pdf"> Monetary Policy Committee Statement </a></td><td>10/8/2026</td></tr>
<tr><td>2.</td><td><a href="/Adverts/PressRelease/en/2026080514165146.pdf">OfficiallaunchoftheTanzaniaSovereignYieldCurve_20260805</a></td><td>8/5/2026</td></tr>
<tr><td>3.</td><td><a href="/Adverts/PressRelease/en/2026080619034782.pdf">Listed on the wrong day</a></td><td>6/8/2026</td></tr>
</table>"""
BOT_SW = b"""<table><tr><td>2.</td><td><a href="/Adverts/PressRelease/sw/2026080514165146.pdf">Uzinduzi wa Mchoro wa Faida Rejea ya Dhamana za Serikali</a></td><td>8/5/2026</td></tr></table>"""

WB = (b'{"rows":3,"documents":{'
      b'"a":{"url":"http://www.worldbank.org/en/country/kenya/publication/kenya-economic-update","lnchdt":"2026-06-29T18:50:00Z",'
      b'"title":{"cdata!":"Kenya Economic Update: inflation and growth"},"descr":{"cdata!":"Growth slowed."}},'
      b'"b":{"url":"https://www.worldbank.org/en/region/sar/publication/south-asia","lnchdt":"2027-04-08T23:00:00Z",'
      b'"title":{"cdata!":"South Asia Economic Update"}},'
      b'"c":{"url":"uz/country/uzbekistan/x","lnchdt":"2026-09-23T08:15:00Z","title":{"cdata!":"Relative link"}},'
      b'"facets":{}}}')


def test_rss_parser_reads_title_link_and_time():
    items = news.parse_rss(RSS)
    assert [i["title"] for i in items] == ["MPC retains the CBR at 8.75 percent", "CEOs Survey of July 2026"]
    assert items[0]["published_at"] == datetime(2026, 10, 7, 16, 3, 48, tzinfo=timezone.utc)


def test_rss_parser_refuses_external_entities():
    evil = b"""<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>
    <rss><channel><item><title>&x;</title><link>https://a</link><pubDate>Wed, 07 Oct 2026 16:03:48 +0000</pubDate></item></channel></rss>"""
    with pytest.raises(Exception):
        news.parse_rss(evil)


def test_bot_dates_come_from_the_file_timestamp_and_must_match_the_listed_date():
    items = news.parse_bot_press(BOT)
    # Row 3's listed date (8 June) contradicts its file timestamp (6 August): skipped, never guessed.
    assert [i["title"] for i in items][:1] == ["Monetary Policy Committee Statement"]
    assert len(items) == 2
    assert items[0]["published_at"].isoformat() == "2026-10-08T15:53:00+03:00"
    assert items[0]["url"] == "https://www.bot.go.tz/Adverts/PressRelease/en/2026100815530593.pdf"


def test_bot_file_name_title_falls_back_to_the_swahili_title():
    merged = news.merge_bot_languages(news.parse_bot_press(BOT), news.parse_bot_press(BOT_SW))
    assert merged[1]["title"].startswith("Uzinduzi wa Mchoro")
    assert merged[1]["language"] == "sw"
    assert "/en/" in merged[1]["url"]  # the link still opens the release


def test_worldbank_parser_keeps_ids_times_and_descriptions():
    items = {i["title"]: i for i in news.parse_worldbank(WB)}
    assert items["Kenya Economic Update: inflation and growth"]["summary"] == "Growth slowed."
    assert news.canonical("http://www.worldbank.org/x?utm_source=rss#top") == "https://www.worldbank.org/x"


def test_rate_decision_is_high_relevance_with_a_stated_reason_and_sector_links():
    t = classify("MPC retains the CBR at 8.75 percent", source_country="KE", securities=SECURITIES)
    assert t.relevance == "HIGH" and t.categories == ["Monetary Policy"] and t.countries == ["KE"]
    assert "asset class" in t.relevance_reason and "Kenya" in t.relevance_reason and "policy rate" in t.relevance_reason
    assert [c["security_id"] for c in t.related["companies"]] == ["NSE:EQTY"]
    assert t.related["companies"][0]["link"] == "sector"
    assert {i["series_id"] for i in t.related["indicators"]} == {"WB_KEN_FP.CPI.TOTL.ZG", "WB_KEN_PA.NUS.FCRF"}


def test_unmatched_story_is_not_assessed_and_links_no_company():
    t = classify("CEOs Survey of July 2026", source_country="KE", securities=SECURITIES)
    assert t.relevance == "NOT_ASSESSED" and t.related["companies"] == []
    t = classify("Nafasi za ajira Benki Kuu ya Tanzania", source_country="TZ", securities=SECURITIES)
    assert t.relevance == "NOT_ASSESSED"  # 'Benki Kuu' is the central bank, a job notice is not banking news


def test_company_is_linked_only_when_named_in_the_headline_or_by_a_banking_rule():
    t = classify("Tanzania Breweries reports half-year results", source_country="TZ", securities=SECURITIES)
    assert [c["security_id"] for c in t.related["companies"]] == ["DSE:TBL"]
    t = classify("Tanzania budget raises excise on beer", source_country="TZ", securities=SECURITIES)
    assert t.related["companies"] == []  # a budget is not a banking rule, and no company is named


def test_story_naming_no_east_african_country_is_not_assessed():
    t = classify("Inflation eases in Europe", source_country=None, securities=SECURITIES)
    assert t.relevance == "NOT_ASSESSED" and t.countries == []


@pytest.fixture()
def client(db, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.setattr(news, "RAW", tmp_path / "raw")
    return TestClient(api.app)


def _source(sid):
    return next(s for s in news.load_sources() if s["id"] == sid)


def test_store_rejects_future_and_relative_items_dedupes_and_updates(db, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.setattr(news, "RAW", tmp_path / "raw")
    when = datetime(2026, 10, 8, 12, tzinfo=timezone.utc)
    with db() as s:
        items = news.parse_worldbank(WB)
        c = news.store(s, _source("worldbank"), WB, items + items, SECURITIES, when)
        s.commit()
        assert c["future_dated"] == 2 and c["stored"] == 1
        assert s.query(NewsItem).count() == 1
        row = s.query(NewsItem).one()
        assert row.summary == "Growth slowed." and row.url.startswith("https://")
        c = news.store(s, _source("worldbank"), WB, items, SECURITIES, when + timedelta(hours=1))
        s.commit()
        assert c["updated"] == 1 and s.query(NewsItem).count() == 1
        # The CBK feed's description is not stored: summary_allowed is false for that source.
        news.store(s, _source("cbk"), RSS, news.parse_rss(RSS), SECURITIES, when)
        s.commit()
        assert all(r.summary is None for r in s.query(NewsItem).filter_by(source_id="cbk"))
        # A Bank of Tanzania time (East Africa Time) is stored as the same instant in UTC.
        news.store(s, _source("bot"), BOT, news.parse_bot_press(BOT), SECURITIES, when)
        s.commit()
        mpc = s.query(NewsItem).filter_by(source_id="bot", title="Monetary Policy Committee Statement").one()
        assert mpc.published_at.replace(tzinfo=None) == datetime(2026, 10, 8, 12, 53)


def test_one_failing_source_does_not_stop_the_others(db, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(news, "RAW", tmp_path / "raw")
    monkeypatch.setattr(news, "SessionLocal", db)

    def fake_fetch(source):
        if source["id"] == "bot":
            raise ConnectionError("timed out")
        return [(RSS, news.parse_rss(RSS))] if source["id"] == "cbk" else [(WB, news.parse_worldbank(WB))]

    monkeypatch.setattr(news, "fetch", fake_fetch)
    assert news.main([]) == 1
    with db() as s:
        assert s.get(DataSourceStatus, "news_bot").status == "failed"
        assert s.get(DataSourceStatus, "news_cbk").status == "ok"
        assert s.query(NewsItem).filter_by(source_id="cbk").count() == 2


def test_api_lists_filters_and_says_when_sources_are_unavailable(client, db, monkeypatch):  # noqa: F811
    monkeypatch.setattr(news, "SessionLocal", db)
    monkeypatch.setattr(news, "fetch", lambda s: (_ for _ in ()).throw(ConnectionError("down")) if s["id"] == "bot"
                        else ([(RSS, news.parse_rss(RSS))] if s["id"] == "cbk" else [(WB, news.parse_worldbank(WB))]))
    news.main([])
    j = client.get("/api/v1/news").json()
    assert j["count"] == 3 and j["some_sources_unavailable"] is True
    assert j["notice"].startswith("Some news sources are temporarily unavailable")
    assert "timed out" not in str(j) and "down" not in j["notice"]  # the error stays on the admin page
    assert client.get("/api/v1/news?country=KE&relevance=HIGH").json()["count"] == 2  # rate decision, inflation update
    assert client.get("/api/v1/news?category=GDP").json()["count"] == 1
    assert client.get("/api/v1/news?country=XX").status_code == 422
    top = client.get("/api/v1/news?relevance=HIGH").json()["items"][0]
    d = client.get(f"/api/v1/news/{top['id']}").json()
    assert d["why_it_matters"] and d["caution"].startswith("Potentially relevant")
    assert all("available" in i for i in d["indicators"])
    assert client.get("/api/v1/news/not-an-id").status_code == 404
    assert client.get("/api/v1/news/" + "0" * 40).status_code == 404


def test_og_image_must_be_https_on_the_publishers_own_site():
    page = '<meta property="og:image" content="https://www.worldbank.org/x/media_1.jpg?width=1200&#x26;format=pjpg">'
    assert news.og_image(page, "https://www.worldbank.org/en/news/a") == "https://www.worldbank.org/x/media_1.jpg?width=1200&format=pjpg"
    assert news.og_image('<meta property="og:image" content="http://169.254.169.254/latest">', "https://www.worldbank.org/a") is None
    assert news.og_image('<meta property="og:image" content="https://evil.example/x.jpg">', "https://www.worldbank.org/a") is None
    assert news.og_image("<p>no image</p>", "https://www.worldbank.org/a") is None
    generic = '<meta property="og:image" content="https://www.worldbank.org/content/dam/wbr/share-logo/social-share.jpg">'
    assert news.og_image(generic, "https://www.worldbank.org/a") is None  # a site logo is not a story image


def test_small_images_are_not_kept(db, monkeypatch):  # noqa: F811
    import io

    from PIL import Image

    def png(w, h):
        b = io.BytesIO(); Image.new("RGB", (w, h)).save(b, "PNG"); return b.getvalue()

    class R:
        def __init__(self, body, ctype):
            self.ok, self.text, self.headers = True, body if isinstance(body, str) else "", {"content-type": ctype}
            self.raw = io.BytesIO(body if isinstance(body, bytes) else b"")
            self.raw.read = (lambda f: (lambda n, decode_content=True: f(n)))(self.raw.read)

    sizes = {"https://www.worldbank.org/a": (1200, 675), "https://www.worldbank.org/b": (600, 400)}

    def fake_get(url, **kw):
        if url.endswith((".png",)):
            return R(png(*sizes[url[:-6]]), "image/png")
        return R(f'<meta property="og:image" content="{url}/i.png">', "text/html")

    monkeypatch.setattr(news.requests, "get", fake_get)
    with db() as s:
        for u in sizes:
            s.add(NewsItem(id=news.item_id(u), source_id="worldbank", title="t", url=u, language="en",
                           published_at=datetime(2026, 10, 1, tzinfo=timezone.utc), retrieved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
                           countries=["KE"], categories=[], relevance="LOW", relevance_reason="r", related={}, raw_sha256="0" * 64))
        s.commit()
        assert news.attach_images(s) == 1
        s.commit()
        kept = {r.url: r.image_url for r in s.query(NewsItem)}
        assert kept["https://www.worldbank.org/a"].endswith("/i.png") and kept["https://www.worldbank.org/b"] is None


def test_an_image_shared_by_several_stories_is_treated_as_generic(db):  # noqa: F811
    with db() as s:
        for i, img in enumerate(["https://www.worldbank.org/a/logo-like.jpg", "https://www.worldbank.org/b/logo-like.jpg", "https://www.worldbank.org/own.jpg"]):
            s.add(NewsItem(id=f"{i:040d}", source_id="worldbank", title="t", url=f"https://www.worldbank.org/{i}", language="en",
                           published_at=datetime(2026, 10, 1, tzinfo=timezone.utc), retrieved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
                           countries=["KE"], categories=[], relevance="LOW", relevance_reason="r", related={}, raw_sha256="0" * 64,
                           image_url=img, image_width=900, image_height=500))
        s.commit()
        assert news.drop_shared_images(s) == 2
        s.commit()
        assert [r.image_url for r in s.query(NewsItem).order_by(NewsItem.id)] == [None, None, "https://www.worldbank.org/own.jpg"]


def test_publisher_images_are_shown_only_when_their_rights_are_permitted(client, db, monkeypatch):  # noqa: F811
    from apps.api.routers import news as news_router

    with db() as s:
        s.add(NewsItem(id="1" * 40, source_id="worldbank", title="Kenya inflation update", url="https://www.worldbank.org/k",
                       language="en", published_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
                       retrieved_at=datetime(2026, 10, 1, tzinfo=timezone.utc), countries=["KE"], categories=["Inflation"],
                       relevance="HIGH", relevance_reason="r", related={}, raw_sha256="0" * 64,
                       image_url="https://www.worldbank.org/i.jpg", image_width=1200, image_height=675,
                       image_checked_at=datetime(2026, 10, 1, tzinfo=timezone.utc)))
        s.commit()
    assert client.get("/api/v1/news").json()["items"][0]["image"] is None  # World Bank: LICENSE_REVIEW_REQUIRED
    real = news_router.news_sources
    monkeypatch.setattr(news_router, "news_sources", lambda: [{**x, "image_rights": "PERMITTED"} if x["id"] == "worldbank" else x for x in real()])
    img = client.get("/api/v1/news").json()["items"][0]["image"]
    assert img["rights"] == "PERMITTED" and img["credit"] == "World Bank" and img["retrieved_at"]
    assert client.get("/api/v1/news?q=inflation").json()["count"] == 1
    assert client.get("/api/v1/news?q=bonds").json()["count"] == 0


def test_library_photos_follow_the_stated_rule_and_carry_their_licence():
    from packages.media import library

    bot = library.for_news("bot", ["TZ"])[0]
    assert bot and bot["kind"] == "library" and bot["caption"].startswith("Bank of Tanzania")
    assert bot["licence"].startswith("CC") and bot["author"] and bot["source_page"].startswith("https://commons.wikimedia.org/")
    wb = library.for_news("worldbank", ["UG", "KE"])
    assert wb[0]["caption"] == "Kampala skyline"  # no institution photo: the first country's city first
    assert any(p["caption"].startswith("Nairobi") for p in wb)
    assert library.for_news("worldbank", []) == []
    assert library.for_security("DSE:NMB")["caption"].startswith("NMB Bank")
    assert library.for_security("DSE:TBL") is None  # no photo of that company, so none is shown
    for e in library._lock().values():
        assert library.ALLOWED_LICENCE.match(e["licence"]), e["licence"]
