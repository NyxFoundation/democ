#!/usr/bin/env python3
"""Count a calendar year's published CVEs mapped by NVD to specified CWEs.

Quarterly queries stay below NVD's 120-day publication window.
The saved snapshot contains query URLs and CVE IDs; it is not an incident count.
Uses curl's system trust configuration, and observes NVD's unauthenticated rate limit.
"""
import argparse
import calendar
import datetime
import json
from pathlib import Path
import subprocess
import time
import urllib.parse

def count(year, cwes, out):
    ids = set()
    queries = []
    for cwe in cwes:
        for month in (1, 4, 7, 10):
            end_month = month + 2
            end_day = calendar.monthrange(year, end_month)[1]
            params = {
                "cweId": cwe,
                "pubStartDate": f"{year}-{month:02}-01T00:00:00.000",
                "pubEndDate": f"{year}-{end_month:02}-{end_day}T23:59:59.999",
                "resultsPerPage": 2000,
            }
            url = "https://services.nvd.nist.gov/rest/json/cves/2.0?" + urllib.parse.urlencode(params)
            matched = set()
            page = 0
            total = None
            while total is None or page < total:
                page_url = url + f"&startIndex={page}"
                raw = subprocess.run(
                    ["curl", "-fLsS", "--retry", "2", "--max-time", "60", page_url],
                    check=True, capture_output=True, text=True).stdout
                data = json.loads(raw)
                total = data["totalResults"]
                values = data["vulnerabilities"]
                for v in values:
                    c = v["cve"]
                    if c.get("vulnStatus") != "Rejected":
                        matched.add(c["id"])
                if not values and page < total:
                    raise RuntimeError("NVD returned an incomplete page")
                page += len(values)
                time.sleep(6)
            ids.update(matched)
            queries.append({"url": url, "total": total, "non_rejected": len(matched)})
            print(cwe, month, len(matched), flush=True)
    snapshot = {"year": year, "cwes": cwes,
                "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "unique_cves": len(ids), "queries": queries, "ids": sorted(ids)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(ids)} unique CVEs → {out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--cwe", nargs="+", default=["CWE-862", "CWE-863"])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    count(a.year, a.cwe, a.out)
