"""Thin client for the Google Trends Compare and Share of Search Tracker Actors on Apify.

The comparison runs on Apify (proxies, Google rate limits and the batch-linking all happen there),
so this package only sends the request and shapes the answer as a pandas DataFrame.
"""
import os

import pandas as pd

COMPARE_ACTOR = "alhadikhan/google-trends-compare"
SHARE_ACTOR = "alhadikhan/share-of-search"
MAX_TERMS = 100
TOKEN_HELP = ("Pass token=... or set the APIFY_TOKEN environment variable. "
              "Get a token at https://console.apify.com/settings/integrations (free account).")


def _get(obj, attr, key):
    """apify-client 3.x returns objects, 2.x returns dicts; read either."""
    return getattr(obj, attr) if hasattr(obj, attr) else obj.get(key)


class Trends:
    def __init__(self, token=None, client=None):
        if client is None:
            from apify_client import ApifyClient

            token = token or os.environ.get("APIFY_TOKEN")
            if not token:
                raise ValueError("No Apify token. " + TOKEN_HELP)
            client = ApifyClient(token)
        self.client = client

    def _run(self, actor, run_input):
        run = self.client.actor(actor).call(run_input=run_input)
        status = _get(run, "status", "status")
        if str(status).split(".")[-1].upper() != "SUCCEEDED":
            message = _get(run, "status_message", "statusMessage")
            raise RuntimeError(f"Run {status}: {message}")
        return list(self.client.dataset(_get(run, "default_dataset_id", "defaultDatasetId")).iterate_items())

    def compare_items(self, keywords, geo="", timeframe="today 12-m", category=0, gprop=""):
        """Raw results: one dict per keyword, with rank, averageInterest, precision and timeline."""
        keywords = [k for k in keywords if k and k.strip()]
        if not keywords:
            raise ValueError("Give at least one keyword")
        if len(keywords) > MAX_TERMS:
            raise ValueError(f"At most {MAX_TERMS} keywords per call (got {len(keywords)})")
        return self._run(COMPARE_ACTOR, {"keywords": keywords, "geo": geo, "timeframe": timeframe,
                                         "category": category, "property": gprop})

    def compare(self, keywords, geo="", timeframe="today 12-m", category=0, gprop=""):
        """All keywords on one 0-100 scale: a DataFrame with dates as rows, keywords as columns."""
        items = self.compare_items(keywords, geo, timeframe, category, gprop)
        by_label = {it["keyword"]: it for it in items}
        order = [k for k in keywords if k in by_label] + [k for k in by_label if k not in keywords]
        first = by_label[order[0]]["timeline"]
        frame = pd.DataFrame({k: [p["value"] for p in by_label[k]["timeline"]] for k in order},
                             index=pd.to_datetime([p["date"] for p in first]))
        frame.index.name = "date"
        frame["isPartial"] = [p["isPartial"] for p in first]
        return frame

    def share_of_search_items(self, brands, geo="", timeframe="today 5-y", period="month", category=0,
                              match_topics=False):
        """Raw results: one dict per brand, with latestShare, changePoints, averageShare and timeline."""
        brands = [b for b in brands if b and b.strip()]
        if len(brands) < 2:
            raise ValueError("Give at least two brands")
        if len(brands) > MAX_TERMS:
            raise ValueError(f"At most {MAX_TERMS} brands per call (got {len(brands)})")
        return self._run(SHARE_ACTOR, {"brands": brands, "geo": geo, "timeframe": timeframe, "period": period,
                                       "category": category, "matchTopics": match_topics})

    def share_of_search(self, brands, geo="", timeframe="today 5-y", period="month", category=0,
                        match_topics=False):
        """Each brand's share (%) of all the brands' searches: periods as rows, brands as columns."""
        items = self.share_of_search_items(brands, geo, timeframe, period, category, match_topics)
        by_brand = {it["brand"]: it for it in items}
        order = [b for b in brands if b in by_brand] + [b for b in by_brand if b not in brands]
        first = by_brand[order[0]]["timeline"]
        frame = pd.DataFrame({b: [p["share"] for p in by_brand[b]["timeline"]] for b in order},
                             index=[p["period"] for p in first])
        frame.index.name = "period"
        frame["isPartial"] = [p["isPartial"] for p in first]
        return frame
