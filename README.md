# pytrends-ladder

**Compare up to 100 Google Trends keywords on one scale.** A pytrends alternative with a drop-in `TrendReq`.

Google Trends compares only 5 terms at a time, and rounds to whole numbers, so small keywords next to big ones show up as 0. `pytrends` was archived in April 2025. This package keeps the familiar `TrendReq` interface, but:

- accepts **up to 100 keywords** and returns them on **one 0–100 scale**;
- keeps **4 decimals**, so small keywords never round to 0;
- runs on [Apify](https://apify.com/alhadikhan/google-trends-compare), which handles proxies and Google's rate limits (no more HTTP 429).

```bash
pip install pytrends-ladder
```

## Switch from pytrends in one line

```python
# from pytrends.request import TrendReq
from pytrends_ladder import TrendReq

pytrends = TrendReq(apify_token="YOUR_APIFY_TOKEN")      # or set APIFY_TOKEN
pytrends.build_payload(["python", "javascript", "java", "typescript", "golang", "kotlin", "haskell"],
                       timeframe="today 12-m", geo="US")   # 7 keywords: more than pytrends' 5
df = pytrends.interest_over_time()                       # dates x keywords + isPartial, one scale
```

`interest_over_time()` is supported. Other pytrends methods (`related_queries`, `interest_by_region`, …) raise `NotImplementedError`.

## Or use the direct API

```python
from pytrends_ladder import Trends

trends = Trends()   # reads APIFY_TOKEN

# Keywords on one scale. Use brackets for one meaning, or Label=TopicID for an exact Google topic
df = trends.compare(["pytorch", "tensorflow", "Python (programming language)", "ChatGPT=/g/11khcfz0y2"])

# Share of search: each brand's % of all the brands' searches, per month, quarter or year
shares = trends.share_of_search(["Samsung", "Vivo", "Apple", "Realme", "Oppo", "Xiaomi"],
                                geo="BD", timeframe="today 5-y", period="quarter")

# Raw results with rank, average interest and a precision label for every keyword
items = trends.compare_items(["weather", "python", "ocaml"])
```

## How accurate is it?

Keywords are sorted by size and compared in linked batches of similar size (a "ladder"). The batches are chained through shared keywords, so even tiny keywords stay measurable.

On real Google data, 12 keywords from "weather" down to "ocaml" (about 5,500x apart):

- no keyword lost;
- neighbouring ratios within 0.5% (median) and 2.2% (worst) of Google's own direct comparisons;
- the same input run twice differed by at most 1.1%.

In the same test, tools that round to whole numbers lost 6 of the 12 keywords.

## Getting a token, and cost

1. Create a free account at [apify.com](https://apify.com).
2. Copy your API token from **Settings → API & Integrations**.

Each call runs an Apify Actor and costs **$0.02 per run + $0.002 per keyword**, or $0.01 per brand for share of search. So 100 keywords cost about $0.22. Apify's free plan includes monthly credit to try it.

## Limits

- Plain words count every meaning: "go" counts the English word, not the language. Use `golang`, a bracket hint like `Python (programming language)`, or a topic ID.
- Values are relative interest (0–100), not search counts. That's what Google Trends provides.
- Up to 100 keywords per call.
- Google serves slightly different samples. Expect around 1% variation between runs.

## License

MIT
