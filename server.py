"""Voice Data Analyst: an MCP server (Streamable HTTP) for Alexa+.

Lets a voice assistant answer spoken questions about CSV datasets in ./data.
Every tool returns a short, speakable sentence plus structured data.
"""
import os
import re
from pathlib import Path

import pandas as pd
from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))

mcp = FastMCP(
    "voice-data-analyst",
    host=os.environ.get("HOST", "0.0.0.0"),
    port=int(os.environ.get("PORT", "8000")),
    stateless_http=True,
)


def _load(name: str) -> pd.DataFrame:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("Dataset names may only contain letters, numbers, - and _.")
    path = DATA_DIR / f"{name}.csv"
    if not path.is_file():
        raise ValueError(f"No dataset called '{name}'. Try list_datasets.")
    df = pd.read_csv(path)
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _col(df: pd.DataFrame, name: str) -> str:
    match = {c.lower(): c for c in df.columns}.get(name.strip().lower())
    if not match:
        raise ValueError(f"Unknown column '{name}'. Columns are: {', '.join(df.columns)}.")
    return match


def _fmt(x: float) -> str:
    return f"{x:,.0f}" if abs(x) >= 100 else f"{x:,.2f}"


@mcp.tool()
def list_datasets() -> dict:
    """List the datasets available to analyze."""
    names = sorted(p.stem for p in DATA_DIR.glob("*.csv"))
    return {"speech": f"I have {len(names)} datasets: {', '.join(names)}." if names
            else "I don't have any datasets yet.", "datasets": names}


@mcp.tool()
def describe_dataset(dataset: str) -> dict:
    """Describe a dataset: row count, columns, and date range if any."""
    df = _load(dataset)
    cols = list(df.columns)
    speech = f"{dataset} has {len(df):,} rows and {len(cols)} columns: {', '.join(cols)}."
    for c in cols:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            speech += f" It runs from {df[c].min():%B %Y} to {df[c].max():%B %Y}."
            break
    return {"speech": speech, "columns": cols, "rows": len(df)}


@mcp.tool()
def top_n(dataset: str, metric: str, group_by: str, n: int = 3, ascending: bool = False) -> dict:
    """Rank groups by a summed metric, e.g. top 3 regions by revenue."""
    df = _load(dataset)
    m, g = _col(df, metric), _col(df, group_by)
    n = max(1, min(int(n), 10))
    s = df.groupby(g)[m].sum().sort_values(ascending=ascending).head(n)
    word = "Lowest" if ascending else "Top"
    parts = [f"{k}, {_fmt(v)}" for k, v in s.items()]
    return {"speech": f"{word} {len(s)} by {m}: " + "; ".join(parts) + ".",
            "results": {str(k): float(v) for k, v in s.items()}}


@mcp.tool()
def trend(dataset: str, metric: str, date_column: str = "date") -> dict:
    """Month-by-month trend of a summed metric, with the overall direction."""
    df = _load(dataset)
    m, d = _col(df, metric), _col(df, date_column)
    s = df.groupby(df[d].dt.to_period("M"))[m].sum()
    if len(s) < 2:
        return {"speech": "There isn't enough history to show a trend.", "series": {}}
    first, last = s.iloc[0], s.iloc[-1]
    change = (last - first) / first * 100 if first else 0.0
    best = s.idxmax()
    direction = "up" if change > 0 else "down"
    speech = (f"{m} is {direction} {abs(change):.0f} percent from {s.index[0]:%B} to "
              f"{s.index[-1]:%B}. The best month was {best:%B}, at {_fmt(s.max())}.")
    return {"speech": speech, "series": {str(k): float(v) for k, v in s.items()}}


@mcp.tool()
def compare(dataset: str, metric: str, group_by: str, first: str, second: str) -> dict:
    """Compare the summed metric of two groups, e.g. South vs North revenue."""
    df = _load(dataset)
    m, g = _col(df, metric), _col(df, group_by)
    s = df.groupby(g)[m].sum()
    lookup = {str(k).lower(): k for k in s.index}
    try:
        a, b = lookup[first.lower()], lookup[second.lower()]
    except KeyError as e:
        raise ValueError(f"Unknown group {e}. Options: {', '.join(map(str, s.index))}.")
    diff = s[a] - s[b]
    lead = a if diff >= 0 else b
    speech = (f"{a} has {_fmt(s[a])} and {b} has {_fmt(s[b])} in {m}. "
              f"{lead} leads by {_fmt(abs(diff))}.")
    return {"speech": speech, "values": {str(a): float(s[a]), str(b): float(s[b])}}


if __name__ == "__main__":
    # Streamable HTTP endpoint is served at http://HOST:PORT/mcp
    mcp.run(transport="streamable-http")
