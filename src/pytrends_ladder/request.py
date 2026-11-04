"""Drop-in for pytrends' TrendReq: change `from pytrends.request import TrendReq` to
`from pytrends_ladder import TrendReq`, and interest_over_time() accepts up to 100 keywords on one scale.
"""
from .client import Trends


class TrendReq:
    def __init__(self, hl="en-US", tz=0, apify_token=None, client=None, **_ignored):
        # hl, tz, proxies, retries and backoff are accepted for compatibility; the Actor handles them
        self._trends = Trends(token=apify_token, client=client)
        self.kw_list, self.cat, self.timeframe, self.geo, self.gprop = [], 0, "today 5-y", "", ""

    def build_payload(self, kw_list, cat=0, timeframe="today 5-y", geo="", gprop=""):
        self.kw_list, self.cat, self.timeframe, self.geo, self.gprop = list(kw_list), cat, timeframe, geo, gprop

    def interest_over_time(self):
        """Like pytrends: dates as rows, one column per keyword plus isPartial; but all on one scale."""
        return self._trends.compare(self.kw_list, geo=self.geo, timeframe=self.timeframe,
                                    category=self.cat, gprop=self.gprop)

    def _unsupported(self, *args, **kwargs):
        raise NotImplementedError("pytrends-ladder supports build_payload() and interest_over_time() only")

    interest_by_region = related_topics = related_queries = trending_searches = _unsupported
    today_searches = realtime_trending_searches = top_charts = suggestions = categories = _unsupported
