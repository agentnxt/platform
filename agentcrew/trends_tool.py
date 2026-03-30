"""
Google Trends tool for CrewAI agents using pytrends (no API key required).
"""
import json
from typing import Optional, Type
from pydantic import BaseModel, Field

try:
    from pytrends.request import TrendReq
    from crewai.tools import BaseTool
except ImportError:
    raise ImportError("pytrends and crewai are required")


class TrendsInput(BaseModel):
    keywords: str = Field(..., description="Comma-separated keywords to analyse (max 5). E.g. 'AI agents, automation'")
    timeframe: Optional[str] = Field("today 3-m", description="Timeframe: 'today 1-m', 'today 3-m', 'today 12-m', 'today 5-y'. Default: today 3-m")
    geo: Optional[str] = Field("", description="Country code e.g. 'US', 'GB'. Empty for worldwide.")


class GoogleTrendsTool(BaseTool):
    name: str = "Google Trends"
    description: str = (
        "Analyse Google Trends for up to 5 keywords. Returns interest over time, "
        "regional breakdown, related topics and related queries. "
        "Use for market research, competitor analysis, content planning and trending topic discovery."
    )
    args_schema: Type[BaseModel] = TrendsInput

    def _run(self, keywords: str, timeframe: str = "today 3-m", geo: str = "") -> str:
        kw_list = [k.strip() for k in keywords.split(",")][:5]
        try:
            pt = TrendReq(hl="en-US", tz=0, timeout=(10, 25))
            pt.build_payload(kw_list, timeframe=timeframe, geo=geo)

            # Interest over time
            iot = pt.interest_over_time()
            if not iot.empty:
                iot = iot.drop(columns=["isPartial"], errors="ignore")
                recent = iot.tail(8).to_dict(orient="index")
                trend_summary = {str(k): v for k, v in recent.items()}
            else:
                trend_summary = {}

            # Related queries
            related = pt.related_queries()
            top_queries = {}
            for kw in kw_list:
                if kw in related and related[kw]["top"] is not None:
                    top_queries[kw] = related[kw]["top"].head(5)["query"].tolist()

            # Regional interest
            by_region = pt.interest_by_region(resolution="COUNTRY", inc_low_vol=False)
            if not by_region.empty:
                top_regions = by_region.sum(axis=1).nlargest(5).index.tolist()
            else:
                top_regions = []

            output = [f"Google Trends analysis for: {', '.join(kw_list)}",
                      f"Timeframe: {timeframe} | Geo: {geo or 'Worldwide'}\n"]

            if trend_summary:
                output.append("── Recent Interest (0-100 scale) ──")
                for date, vals in list(trend_summary.items())[-4:]:
                    row = ", ".join(f"{k}: {v}" for k, v in vals.items())
                    output.append(f"  {date[:10]}: {row}")

            if top_queries:
                output.append("\n── Top Related Queries ──")
                for kw, queries in top_queries.items():
                    output.append(f"  {kw}: {', '.join(queries)}")

            if top_regions:
                output.append(f"\n── Top Regions: {', '.join(top_regions)}")

            return "\n".join(output)

        except Exception as exc:
            return f"Google Trends query failed: {exc}"
