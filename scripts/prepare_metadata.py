"""Prepare verified canonical Surah and Quranic structural metadata.

Parses data/raw/quran-data.xml to generate data/surah_metadata.json:
- 114 Surahs with Arabic, English transliteration, English translation,
  revelation order, revelation place, total ayahs, start page, start juz,
  and Bismillah presence flag.
- 15 Sajdah locations with exact Surah, Ayah, and classification.
- Page, Juz, Manzil, and Hizb boundary mappings.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings


def generate_metadata() -> None:
    xml_path = settings.RAW_DATA_DIR / settings.TANZIL_METADATA_XML_FILE
    target_json_path = settings.DATA_DIR / settings.SURAH_METADATA_FILE

    if not xml_path.exists():
        print(f"[ERROR] Source XML metadata file not found at {xml_path}.")
        print("Please run `python scripts/download_data.py` first.")
        sys.exit(1)

    print(f"Parsing canonical metadata from: {xml_path}")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 1. Parse Pages (1 to 604)
    pages = []
    for p in root.findall(".//page"):
        pages.append({
            "page": int(p.attrib["index"]),
            "sura": int(p.attrib["sura"]),
            "aya": int(p.attrib["aya"]),
        })

    # 2. Parse Juzs (1 to 30)
    juzs = []
    for j in root.findall(".//juz"):
        juzs.append({
            "juz": int(j.attrib["index"]),
            "sura": int(j.attrib["sura"]),
            "aya": int(j.attrib["aya"]),
        })

    # 3. Parse Manzils (1 to 7)
    manzils = []
    for m in root.findall(".//manzil"):
        manzils.append({
            "manzil": int(m.attrib["index"]),
            "sura": int(m.attrib["sura"]),
            "aya": int(m.attrib["aya"]),
        })

    # 4. Parse Hizb Quarters (1 to 240)
    hizbs = []
    for h in root.findall(".//quarter"):
        hizbs.append({
            "quarter": int(h.attrib["index"]),
            "sura": int(h.attrib["sura"]),
            "aya": int(h.attrib["aya"]),
        })

    # 5. Parse Sajdas (15)
    sajdas = []
    for s in root.findall(".//sajda"):
        sajdas.append({
            "sura": int(s.attrib["sura"]),
            "aya": int(s.attrib["aya"]),
            "type": s.attrib.get("type", "recommended").lower(),
        })

    def get_page_for_verse(sura_id: int, aya_num: int) -> int:
        curr = 1
        for p in pages:
            if (p["sura"] < sura_id) or (p["sura"] == sura_id and p["aya"] <= aya_num):
                curr = p["page"]
            else:
                break
        return curr

    def get_juz_for_verse(sura_id: int, aya_num: int) -> int:
        curr = 1
        for j in juzs:
            if (j["sura"] < sura_id) or (j["sura"] == sura_id and j["aya"] <= aya_num):
                curr = j["juz"]
            else:
                break
        return curr

    # 6. Parse all 114 Surahs
    surahs_list = []
    total_quran_ayahs = 0

    for s in root.findall(".//sura"):
        idx = int(s.attrib["index"])
        name_ar = s.attrib["name"]
        name_en = s.attrib["tname"]
        name_trans = s.attrib["ename"]
        rev_place = "makkah" if s.attrib["type"].lower() == "meccan" else "madinah"
        order = int(s.attrib["order"])
        total_ayahs = int(s.attrib["ayas"])
        total_quran_ayahs += total_ayahs

        # Surah 9 (At-Tawbah) has no Bismillah
        has_bismillah = (idx != 9)
        start_page = get_page_for_verse(idx, 1)
        start_juz = get_juz_for_verse(idx, 1)

        surahs_list.append({
            "id": idx,
            "name_ar": name_ar,
            "name_en": name_en,
            "name_transliteration": name_trans,
            "revelation_place": rev_place,
            "revelation_order": order,
            "total_ayahs": total_ayahs,
            "has_bismillah": has_bismillah,
            "start_page": start_page,
            "start_juz": start_juz,
        })

    # Assertions
    assert len(surahs_list) == 114, f"Expected 114 surahs, got {len(surahs_list)}"
    assert total_quran_ayahs == 6236, f"Expected 6236 total ayahs, got {total_quran_ayahs}"
    assert len(pages) == 604, f"Expected 604 pages, got {len(pages)}"
    assert len(juzs) == 30, f"Expected 30 juzs, got {len(juzs)}"
    assert len(sajdas) == 15, f"Expected 15 sajdas, got {len(sajdas)}"
    assert surahs_list[8]["has_bismillah"] is False, "Surah 9 must have has_bismillah = False"
    assert surahs_list[0]["has_bismillah"] is True, "Surah 1 must have has_bismillah = True"

    payload = {
        "version": "1.0",
        "description": "Canonical Quran & Surah Metadata derived from Tanzil Project",
        "total_surahs": len(surahs_list),
        "total_ayahs": total_quran_ayahs,
        "surahs": surahs_list,
        "sajdas": sajdas,
        "pages_count": len(pages),
        "juzs_count": len(juzs),
        "pages_index": pages,
        "juzs_index": juzs,
        "manzils_index": manzils,
        "hizb_quarters_index": hizbs,
    }

    target_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    size_kb = target_json_path.stat().st_size / 1024
    print(f"[SUCCESS] Curated {target_json_path.name} ({size_kb:.1f} KB)")
    print(f"  - 114 Surahs verified (Total Ayahs: {total_quran_ayahs})")
    print(f"  - 15 Sajdah verses mapped")
    print(f"  - 604 Pages indexed")
    print(f"  - 30 Juzs indexed")


if __name__ == "__main__":
    generate_metadata()
