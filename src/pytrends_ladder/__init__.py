"""Compare up to 100 Google Trends keywords on one scale. A pytrends alternative."""
from .client import Trends
from .request import TrendReq

__all__ = ["Trends", "TrendReq"]
__version__ = "0.1.0"
