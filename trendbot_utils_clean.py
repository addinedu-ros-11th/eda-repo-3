
# trendbot_utils_clean.py
# Refactored to remove hidden globals and make dependencies explicit.
# Safe defaults are provided; callers should pass config/args explicitly for reproducibility.
from __future__ import annotations
from typing import Iterable, Sequence, Optional, Dict, Any, List, Tuple
import os, json, time, math, subprocess, sys
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt

# -----------------------------
# Session / HTTP helpers
# -----------------------------
def make_session(token: Optional[str] = None, base_headers: Optional[Dict[str, str]] = None) -> requests.Session:
    """Create a requests.Session with GitHub token if provided."""
    s = requests.Session()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "trendbot-utils/1.0"
    }
    if base_headers:
        headers.update(base_headers)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    s.headers.update(headers)
    return s

def gh_get(session: requests.Session, url: str, params: Optional[Dict[str, Any]] = None,
           max_retries: int = 3, sleep: float = 1.0) -> requests.Response:
    """GET with simple retry & rate limit handling (explicit session)."""
    last = None
    for i in range(max_retries):
        resp = session.get(url, params=params, timeout=30)
        last = resp
        # Rate limit handling
        if resp.status_code == 403 and 'rate limit' in resp.text.lower():
            reset = resp.headers.get('X-RateLimit-Reset')
            wait_s = max(5, (int(reset) - int(time.time())) + 1) if reset and reset.isdigit() else 10
            time.sleep(wait_s)
            continue
        try:
            resp.raise_for_status()
            return resp
        except requests.HTTPError:
            if i == max_retries - 1:
                raise
            time.sleep(sleep)
    assert last is not None
    return last

# -----------------------------
# GitHub search helpers
# -----------------------------
def search_repos(session: requests.Session, q: str, *, sort: str = "stars", order: str = "desc",
                 per_page: int = 50, pages: int = 1) -> List[Dict[str, Any]]:
    """Search popular repositories by query. Returns list[dict]."""
    items: List[Dict[str, Any]] = []
    for page in range(1, pages + 1):
        resp = gh_get(session, "https://api.github.com/search/repositories", {
            "q": q, "sort": sort, "order": order, "per_page": per_page, "page": page
        })
        js = resp.json()
        batch = js.get("items", []) or []
        items.extend(batch)
        if len(batch) < per_page:
            break
    return items

# -----------------------------
# Pandas helpers
# -----------------------------
def safe_dt(s) -> pd.Timestamp | pd.NaT:
    if not s:
        return pd.NaT
    try:
        return pd.to_datetime(s, utc=True, errors="coerce")
    except Exception:
        return pd.NaT

def to_row(o: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": o.get("id"),
        "full_name": o.get("full_name"),
        "description": o.get("description"),
        "language": o.get("language"),
        "stargazers_count": o.get("stargazers_count", 0),
        "forks_count": o.get("forks_count", 0),
        "open_issues_count": o.get("open_issues_count", 0),
        "created_at": safe_dt(o.get("created_at")),
        "updated_at": safe_dt(o.get("updated_at")),
        "topics": ",".join(o.get("topics", [])),
        "fork": bool(o.get("fork", False)),
    }

def top_with_other(s: pd.Series, top_n: int = 12, other: str = "Other") -> pd.Series:
    vc = s.value_counts(dropna=False)
    if len(vc) <= top_n:
        return vc
    return pd.concat([vc.iloc[:top_n], pd.Series({other: vc.iloc[top_n:].sum()})])

# -----------------------------
# Analysis / plotting
# -----------------------------
def ensure_last_active(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure a tz-aware 'last_active' column exists."""
    out = df.copy()
    if "last_active" not in out.columns:
        for col in ["created_at", "updated_at", "pushed_at", "last_commit_at"]:
            if col not in out.columns:
                out[col] = pd.NaT
            out[col] = pd.to_datetime(out[col], errors="coerce", utc=True)
        out["last_active"] = out[["pushed_at","updated_at","last_commit_at","created_at"]].max(axis=1)
    return out

def plot_recent_window(df: pd.DataFrame, *, window_days: int, top_k: int = 20,
                       label_col: str = "query_source", stars_col: str = "stargazers_count"):
    """Visualize median stars for top_k label groups within a recent time window."""
    df2 = ensure_last_active(df)
    now_utc = pd.Timestamp.now(tz="UTC")
    recent_cut = now_utc - pd.Timedelta(days=window_days)
    sub = df2[df2["last_active"].notna() & (df2["last_active"] >= recent_cut)].copy()
    if len(sub) == 0:
        print(f"[INFO] No rows in the last {window_days} days. Skip.")
        return None

    top_lbls = sub[label_col].value_counts().head(top_k).index
    med = (sub[sub[label_col].isin(top_lbls)]
           .groupby(label_col)[stars_col]
           .median()
           .sort_values())

    plt.figure()
    med.plot(kind="barh")
    plt.title(f"[RECENT {window_days}d] Median Stars — Top {top_k} by Recent Activity")
    plt.xlabel("Median Stars (recent window)")
    plt.tight_layout()
    plt.show()

    summary = (sub[sub[label_col].isin(top_lbls)]
               .groupby(label_col)
               .agg(repos=("full_name", "count"),
                    stars_median=(stars_col, "median"),
                    stars_mean=(stars_col, "mean"))
               .sort_values("repos", ascending=False))
    return list(top_lbls), summary

def ensure_top_count(df: pd.DataFrame, *, label_col: str = "query_source", top_k: int = 20) -> List[str]:
    return list(df[label_col].value_counts().head(top_k).index)

def ensure_top_total_stars(df: pd.DataFrame, *, label_col: str = "query_source",
                           stars_col: str = "stargazers_count", top_k: int = 20) -> List[str]:
    s = df.groupby(label_col)[stars_col].sum().sort_values(ascending=False)
    return list(s.head(top_k).index)

def ensure_tops_by_window(df: pd.DataFrame, *, windows: Sequence[int] = (7, 30, 90),
                          label_col: str = "query_source", top_k: int = 20) -> Dict[int, List[str]]:
    df2 = ensure_last_active(df)
    now_utc = pd.Timestamp.now(tz="UTC")
    out: Dict[int, List[str]] = {}
    for w in windows:
        cut = now_utc - pd.Timedelta(days=w)
        sub = df2[df2["last_active"].notna() & (df2["last_active"] >= cut)]
        if len(sub) == 0:
            out[w] = []
        else:
            out[w] = list(sub[label_col].value_counts().head(top_k).index)
    return out

# -----------------------------
# Overlap / scoring helpers
# -----------------------------
def jaccard(a: set, b: set) -> float:
    if len(a) == 0 and len(b) == 0:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0

def summarize_candidates(df: pd.DataFrame, items: Sequence[str], *, label_col: str = "query_source",
                         stars_col: str = "stargazers_count",
                         overlap_mat: Optional[pd.DataFrame] = None,
                         criteria: Optional[Sequence[str]] = None) -> pd.DataFrame:
    """Summarize candidate groups. If overlap_mat & criteria are supplied,
    include per-criterion inclusion columns and overlap_count."""
    sub = df[df[label_col].isin(items)].copy()
    agg = (sub.groupby(label_col)
              .agg(repos=("full_name", "count"),
                   stars_sum=(stars_col, "sum"),
                   stars_mean=(stars_col, "mean"),
                   stars_median=(stars_col, "median"),
                   last_active_max=("last_active", "max"),
                   languages_uniq=("language", "nunique")))

    if overlap_mat is not None and criteria is not None:
        crit_cols = []
        for crit in criteria:
            col = f"in_{crit}"
            agg[col] = overlap_mat.loc[agg.index, crit].astype(int).reindex(agg.index).fillna(0).astype(int)
            crit_cols.append(col)
        agg["overlap_count"] = agg[crit_cols].sum(axis=1)
        agg["included_criteria"] = [
            ", ".join([c for c in criteria if overlap_mat.loc[item, c] == 1]) for item in agg.index
        ]

        agg = agg.sort_values(by=["overlap_count", "stars_median", "repos"],
                              ascending=[False, False, False])
    else:
        agg = agg.sort_values(by=["stars_median", "repos"], ascending=[False, False])
    return agg

def select_overlap_candidates(overlap_mat: pd.DataFrame, *, min_criteria: int = 2) -> List[str]:
    mask = overlap_mat.sum(axis=1) >= min_criteria
    return list(overlap_mat.index[mask])

# -----------------------------
# GitHub counters
# -----------------------------
def paged_count(session: requests.Session, url: str, params: Dict[str, Any], *, pages: int = 5) -> int:
    total = 0
    for page in range(1, pages + 1):
        p = dict(params)
        p.update({"per_page": 100, "page": page})
        r = gh_get(session, url, p)
        arr = r.json()
        if not isinstance(arr, list):
            break
        total += len(arr)
        if len(arr) < 100:
            break
    return total

def count_closed(session: requests.Session, url: str, params: Dict[str, Any], *, is_pr: bool = False) -> Tuple[int, int]:
    p = dict(params)
    p.update({"per_page": 100, "page": 1, "state": "closed"})
    r = gh_get(session, url, p)
    arr = r.json()
    if not isinstance(arr, list):
        return 0, 0
    closed = len(arr)
    merged = 0
    if is_pr:
        merged = sum(1 for x in arr if x.get("merged_at"))
    return closed, merged

# -----------------------------
# Math helpers
# -----------------------------
def recent_push_90d(ts) -> bool:
    if pd.isna(ts):
        return False
    return (pd.Timestamp.now(tz=timezone.utc) - ts).days <= 90

def safe_rate(numer: pd.Series, denom: pd.Series) -> pd.Series:
    numer = numer.fillna(0)
    denom = denom.fillna(0)
    with np.errstate(divide='ignore', invalid='ignore'):
        r = np.where(denom > 0, numer / denom, 0.0)
    return pd.Series(r, index=numer.index, dtype=float)

def normalize(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").fillna(0)
    vmax, vmin = float(s.max()), float(s.min())
    if vmax == vmin:
        return pd.Series(0.0, index=s.index)
    return (s - vmin) / (vmax - vmin)

def rubric_row(name: str, desc: Optional[str]) -> Dict[str, Any]:
    base = {"repo": name, "readme_score": 16, "test_score": 12, "doc_score": 12,
            "contributors_score": 12, "activity_score": 12, "license_score": 10, "ci_score": 5}
    L = len((desc or "").split())
    if L > 12: base["readme_score"] += 2
    return base
