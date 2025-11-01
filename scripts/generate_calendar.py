#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a public ICS calendar of famous artists' birthdays and death anniversaries (daily),
sourced from Wikidata via SPARQL.

Outputs a single .ics file with all-day events for today's date (month/day),
optionally for a different date via --date YYYY-MM-DD.

Author: TV Wien / TV Beč
"""

import argparse
import os
import sys
import json
import datetime as dt
import pytz
import requests
from urllib.parse import quote

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

def load_occupations(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return list(data.values())  # return QIDs list

def build_sparql_query(occ_qids, month, day, lang="en", mode="births"):
    """
    mode: 'births' or 'deaths'
    """
    date_prop = "wdt:P569" if mode == "births" else "wdt:P570"
    occ_filter = " ".join([f"wd:{qid}" for qid in occ_qids])
    label_lang = lang  # e.g., 'hr', 'de', 'en'

    query = f"""
    SELECT ?person ?personLabel ?date ?occLabel WHERE {{
      ?person wdt:P31 wd:Q5 .
      OPTIONAL {{ ?person {date_prop} ?date . }}
      ?person wdt:P106 ?occ .
      FILTER(?occ IN ({occ_filter}))
      FILTER(MONTH(?date) = {month} && DAY(?date) = {day})
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{label_lang},en".
        ?person rdfs:label ?personLabel.
        ?occ rdfs:label ?occLabel.
      }}
    }}
    ORDER BY ?personLabel
    """
    return query

def run_sparql(query):
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "TVWien-CulturalCalendar/1.0 (https://tvwien.at)"
    }
    resp = requests.get(SPARQL_ENDPOINT, params={"query": query}, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()

def sanitize_text(s):
    if not s:
        return ""
    # Basic escape for ICS text
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def dtstamp():
    return dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def ical_header(title="TV Wien – Kulturni kalendar", tz="Europe/Vienna"):
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//TV Wien//Cultural Calendar//HR
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{sanitize_text(title)}
X-WR-TIMEZONE:{tz}
"""

def ical_footer():
    return "END:VCALENDAR\n"

def make_event(date, summary, description, uid):
    # All-day event
    dstr = date.strftime("%Y%m%d")
    return f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp()}
DTSTART;VALUE=DATE:{dstr}
DTEND;VALUE=DATE:{(date + dt.timedelta(days=1)).strftime("%Y%m%d")}
SUMMARY:{sanitize_text(summary)}
DESCRIPTION:{sanitize_text(description)}
END:VEVENT
"""

def parse_args():
    ap = argparse.ArgumentParser(description="Generate TV Wien cultural ICS for today's anniversaries.")
    ap.add_argument("--out", default="public/tvwien_cultural_calendar.ics", help="Output ICS path")
    ap.add_argument("--date", default=None, help="Use a specific date YYYY-MM-DD (default: today local)")
    ap.add_argument("--lang", default=os.getenv("LANG", "hr"), choices=["hr", "de", "en"], help="Language for labels")
    ap.add_argument("--title", default=os.getenv("TITLE", "TV Wien – Kulturni kalendar"))
    ap.add_argument("--tz", default=os.getenv("TZ", "Europe/Vienna"))
    ap.add_argument("--occupations", default="config/occupations.json", help="Path to occupations JSON")
    return ap.parse_args()

def main():
    args = parse_args()
    # Determine the date (local Europe/Vienna by default)
    tz = pytz.timezone(args.tz)
    if args.date:
        y, m, d = map(int, args.date.split("-"))
        target = tz.localize(dt.datetime(y, m, d))
    else:
        target = dt.datetime.now(tz)

    month = target.month
    day = target.day

    occ_qids = load_occupations(args.occupations)

    # Prepare ICS buffer
    ics = []
    ics.append(ical_header(args.title, tz=args.tz))

    # Query births
    births_q = build_sparql_query(occ_qids, month, day, lang=args.lang, mode="births")
    births = run_sparql(births_q)
    # Query deaths
    deaths_q = build_sparql_query(occ_qids, month, day, lang=args.lang, mode="deaths")
    deaths = run_sparql(deaths_q)

    # Helpers for summaries
    def birth_summary(name, year, occ):
        # Emojis neutral; localized keywords
        label = {"hr": "Rođendan", "de": "Geburtstag", "en": "Birthday"}.get(args.lang, "Rođendan")
        return f"🎉 {label}: {name} ({year}) – {occ}" if year else f"🎉 {label}: {name} – {occ}"

    def death_summary(name, year, occ):
        label = {"hr": "Obljetnica smrti", "de": "Todestag", "en": "Death anniversary"}.get(args.lang, "Obljetnica smrti")
        return f"✝️ {label}: {name} ({year}) – {occ}" if year else f"✝️ {label}: {name} – {occ}"

    # Process results
    for row in births.get("results", {}).get("bindings", []):
        name = row.get("personLabel", {}).get("value")
        date_val = row.get("date", {}).get("value")
        occ = row.get("occLabel", {}).get("value")
        entity = row.get("person", {}).get("value")
        year = None
        if date_val and len(date_val) >= 4:
            year = date_val[:4]
        summary = birth_summary(name, year, occ)
        desc = f"{name} – {occ}\\nWikidata: {entity}"
        uid = f"{month:02d}{day:02d}-B-{quote(entity)}"
        ics.append(make_event(target.date(), summary, desc, uid))

    for row in deaths.get("results", {}).get("bindings", []):
        name = row.get("personLabel", {}).get("value")
        date_val = row.get("date", {}).get("value")
        occ = row.get("occLabel", {}).get("value")
        entity = row.get("person", {}).get("value")
        year = None
        if date_val and len(date_val) >= 4:
            year = date_val[:4]
        summary = death_summary(name, year, occ)
        desc = f"{name} – {occ}\\nWikidata: {entity}"
        uid = f"{month:02d}{day:02d}-D-{quote(entity)}"
        ics.append(make_event(target.date(), summary, desc, uid))

    ics.append(ical_footer())

    # Ensure output directory
    out_path = args.out
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(ics))

    print(f"Generated ICS with {len(ics)-2} events → {out_path}")

if __name__ == "__main__":
    main()
