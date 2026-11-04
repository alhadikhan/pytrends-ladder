"""Offline tests with a fake Apify client shaped like apify-client 3.x (objects) and 2.x (dicts)."""
from types import SimpleNamespace

import pytest

from pytrends_ladder import Trends, TrendReq

TL = [{"date": "2026-01-04", "value": 1.0, "isPartial": False}, {"date": "2026-01-11", "value": 2.0, "isPartial": True}]


def item(label, scale):
    return {"rank": 1, "keyword": label, "averageInterest": 1.5 * scale,
            "timeline": [{**p, "value": p["value"] * scale} for p in TL]}


class FakeClient:
    def __init__(self, items, status="SUCCEEDED", as_dict=False):
        self.items, self.status, self.as_dict, self.calls = items, status, as_dict, []

    def actor(self, actor_id):
        def call(run_input):
            self.calls.append((actor_id, run_input))
            if self.as_dict:
                return {"status": self.status, "statusMessage": "boom", "defaultDatasetId": "d1"}
            return SimpleNamespace(status=self.status, status_message="boom", default_dataset_id="d1")
        return SimpleNamespace(call=call)

    def dataset(self, dataset_id):
        return SimpleNamespace(iterate_items=lambda: iter(self.items))


@pytest.mark.parametrize("as_dict", [False, True])
def test_compare_keeps_input_order_and_marks_partial(as_dict):
    fake = FakeClient([item("rust", 10), item("python", 50)], as_dict=as_dict)
    df = Trends(client=fake).compare(["python", "rust"], geo="US")
    assert list(df.columns) == ["python", "rust", "isPartial"]
    assert df["python"].tolist() == [50.0, 100.0] and df["isPartial"].tolist() == [False, True]
    assert str(df.index[0].date()) == "2026-01-04"
    assert fake.calls[0][0] == "alhadikhan/google-trends-compare" and fake.calls[0][1]["geo"] == "US"


def test_trendreq_is_a_drop_in_for_interest_over_time():
    fake = FakeClient([item(k, s) for k, s in [("a", 1), ("b", 2), ("c", 3), ("d", 4), ("e", 5), ("f", 6)]])
    pt = TrendReq(hl="en-US", tz=360, client=fake, retries=3, backoff_factor=0.5)
    pt.build_payload(["a", "b", "c", "d", "e", "f"], timeframe="today 12-m", geo="GB")   # 6 > pytrends' 5
    df = pt.interest_over_time()
    assert list(df.columns)[:6] == ["a", "b", "c", "d", "e", "f"]
    assert fake.calls[0][1]["timeframe"] == "today 12-m" and fake.calls[0][1]["geo"] == "GB"
    with pytest.raises(NotImplementedError):
        pt.related_queries()


def test_share_of_search_frame():
    items = [{"brand": b, "timeline": [{"period": "2026-Q1", "share": s, "isPartial": False}]} for b, s in [("B", 40.0), ("A", 60.0)]]
    df = Trends(client=FakeClient(items)).share_of_search(["A", "B"], geo="BD", period="quarter")
    assert list(df.columns) == ["A", "B", "isPartial"] and df.loc["2026-Q1", "A"] == 60.0


def test_failed_run_raises_with_the_actor_message():
    with pytest.raises(RuntimeError, match="boom"):
        Trends(client=FakeClient([], status="FAILED")).compare(["x"])


def test_input_checks(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    with pytest.raises(ValueError, match="APIFY_TOKEN"):
        Trends()
    t = Trends(client=FakeClient([]))
    with pytest.raises(ValueError):
        t.compare([])
    with pytest.raises(ValueError):
        t.compare([f"k{i}" for i in range(101)])
    with pytest.raises(ValueError):
        t.share_of_search(["only one"])
