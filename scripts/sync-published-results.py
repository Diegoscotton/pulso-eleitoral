#!/usr/bin/env python3
"""Build a source-linked snapshot of published 2026 poll results.

The TSE open-data file is used only to validate protocol, sample and office.
Percentages come from a public research archive that links each scenario to its
underlying publication. Unregistered or unmatched scenarios are excluded.
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
POLL_FILE = ROOT / "public/data/2026.json"
CANDIDATE_FILE = ROOT / "public/data/candidates-2026.json"
OUTPUT_FILE = ROOT / "public/data/2026-results.json"
ARCHIVE_URL = "https://depoisdas17.com.br/pesquisas/"
ARCHIVE_BASE = "https://depoisdas17.com.br"


class ArchiveProps(HTMLParser):
    props: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "astro-island" and "TabelaPesquisas" in (values.get("component-url") or ""):
            self.props = values.get("props")


def decode_devalue(value):
    """Decode the small tagged tuple format used in the archive's Astro props."""
    if isinstance(value, list) and len(value) == 2 and value[0] in (0, 1):
        if value[0] == 0:
            return decode_devalue(value[1])
        if isinstance(value[1], list):
            return [decode_devalue(item) for item in value[1]]
    if isinstance(value, dict):
        return {key: decode_devalue(item) for key, item in value.items()}
    if isinstance(value, list):
        return [decode_devalue(item) for item in value]
    return value


def key(value: str) -> str:
    value = unicodedata.normalize("NFD", value or "")
    return re.sub(r"[^A-Z0-9]+", "", "".join(c for c in value if not unicodedata.combining(c)).upper())


def protocol_key(value: str) -> str:
    return key(value)


def fetch_archive() -> dict:
    request = urllib.request.Request(ARCHIVE_URL, headers={"User-Agent": "PulsoEleitoral/1.0 (public poll results snapshot)"})
    with urllib.request.urlopen(request, timeout=45) as response:
        page = response.read().decode("utf-8")
    parser = ArchiveProps()
    parser.feed(page)
    if not parser.props:
        raise RuntimeError("O acervo público não apresentou os dados de cenários esperados.")
    props = json.loads(parser.props)
    decoded = decode_devalue(props["dados"])
    if len(decoded.get("linhas", [])) < 100 or not decoded.get("recortes"):
        raise RuntimeError("A estrutura do acervo mudou ou veio incompleta; snapshot preservado.")
    return decoded


def candidate_parties(records: list[dict]) -> list[dict]:
    return [{"id": candidate.get("id", ""), "aliases": {key(candidate.get("name", "")), key(candidate.get("fullName", ""))} - {""}, "party": candidate.get("party", ""), "office": candidate.get("office", ""), "uf": candidate.get("uf", "")} for candidate in records]


def infer_party(name: str, entries: list[dict], office: str, uf: str) -> str | None:
    normalized = key(name)
    query_words = set(re.findall(r"[A-Z0-9]+", normalized))
    scoped_uf = "BR" if office == "Presidente" else uf
    scoped = [candidate for candidate in entries if candidate["office"] == office and candidate["uf"] == scoped_uf and candidate["party"]]
    exact = [candidate for candidate in scoped if normalized in candidate["aliases"]]
    matches = exact or ([candidate for candidate in scoped if len(query_words) >= 2 and any(query_words <= set(re.findall(r"[A-Z0-9]+", alias)) for alias in candidate["aliases"])] if query_words else [])
    party_matches = {candidate["party"] for candidate in matches}
    return next(iter(party_matches)) if len(party_matches) == 1 else None


def main() -> None:
    if not POLL_FILE.exists():
        raise RuntimeError("A base oficial TSE de 2026 precisa ser baixada antes desta rotina.")
    polls = json.loads(POLL_FILE.read_text()).get("records", [])
    party_file = Path("/tmp/candidate-party-index-2026.json")
    candidates = json.loads(party_file.read_text()).get("records", []) if party_file.exists() else (json.loads(CANDIDATE_FILE.read_text()).get("records", []) if CANDIDATE_FILE.exists() else [])
    by_protocol = {protocol_key(row.get("id", "")): row for row in polls if row.get("id")}
    parties = candidate_parties(candidates)
    archive = fetch_archive()
    institutes, contractors = archive["institutos"], archive["contratantes"]
    candidate_names, recortes = archive["candidatos"], archive["recortes"]
    stats = {name: 0 for name in ("archive_scenarios", "published_registered", "excluded_no_protocol", "excluded_no_tse_record", "excluded_sample_mismatch", "excluded_date_mismatch", "excluded_office_mismatch", "excluded_without_source")}
    output = []
    for line in archive["linhas"]:
        stats["archive_scenarios"] += 1
        # [slug, institute, contractor, turn, field-date, n, margin, protocol,
        #  independent-source count, [[candidate-index, pct], ...], recorte-index]
        if len(line) != 11:
            continue
        slug, institute_i, contractor_i, turn, field_date, sample, margin, protocol, source_count, result_pairs, recorte_i = line
        if not protocol:
            stats["excluded_no_protocol"] += 1
            continue
        official = by_protocol.get(protocol_key(protocol))
        if not official:
            stats["excluded_no_tse_record"] += 1
            continue
        if float(official.get("sample", 0) or 0) != float(sample or 0):
            stats["excluded_sample_mismatch"] += 1
            continue
        if not official.get("start") or not official.get("end") or not official["start"] <= field_date <= official["end"]:
            stats["excluded_date_mismatch"] += 1
            continue
        recorte = recortes[recorte_i]
        office = {"presidente": "Presidente", "governador": "Governador", "senador": "Senador", "deputadofederal": "Deputado Federal", "deputadoestadual": "Deputado Estadual", "deputadodistrital": "Deputado Distrital"}.get(key(recorte.get("cargo", "")).lower())
        if not office or office not in official.get("offices", []):
            stats["excluded_office_mismatch"] += 1
            continue
        if not source_count:
            stats["excluded_without_source"] += 1
            continue
        result_candidates = []
        for candidate_i, percentage in result_pairs:
            if not isinstance(candidate_i, int) or not isinstance(percentage, (int, float)) or not 0 <= percentage <= 100:
                continue
            name = candidate_names[candidate_i]
            result_candidates.append({"name": name, "party": infer_party(name, parties, office, recorte.get("uf") or "BR"), "percentage": percentage})
        if not result_candidates:
            continue
        record = {
            "id": slug,
            "office": office,
            "uf": recorte.get("uf") or "BR",
            "scope": recorte.get("longo") or recorte.get("curto"),
            "turn": int(turn),
            "fieldDate": field_date,
            "institute": institutes[institute_i],
            "contractor": contractors[contractor_i] if isinstance(contractor_i, int) and contractor_i >= 0 else None,
            "sample": sample,
            "margin": margin,
            "protocol": official.get("id"),
            "protocolDisplay": protocol,
            "registeredUf": official.get("uf"),
            "candidates": result_candidates,
            "archiveUrl": f"{ARCHIVE_BASE}/pesquisas/{slug}/",
            "sourceUrl": ARCHIVE_URL,
            "sourceCount": int(source_count),
            "sourceProvenance": "consulte a ficha vinculada para a publicação de origem",
        }
        output.append(record)
        stats["published_registered"] += 1
    if len(output) < 25:
        raise RuntimeError(f"Só {len(output)} cenários passaram a validação TSE; snapshot preservado.")
    output.sort(key=lambda item: (item["fieldDate"], item["sample"]), reverse=True)
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": ARCHIVE_URL,
        "registrySource": "https://dadosabertos.tse.jus.br/dataset/pesquisas-eleitorais-2026",
        "validation": "protocol and declared sample matched to the official TSE 2026 registry; source link retained for each scenario",
        "stats": stats,
        "records": output,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({**stats, "output": str(OUTPUT_FILE), "records": len(output)}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"sync-published-results: {exc}", file=sys.stderr)
        raise
