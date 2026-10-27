"""Database Seeding Pipeline for Wird Quran Engine.

Populates the database with:
1. 114 Surahs with metadata, revelation order, page/juz bounds, and Bismillah flags.
2. 6,236 Ayahs with Uthmanic and simplified text, Sajdah marks, and page/juz boundaries.
3. 12,472 Translations (English Saheeh International + Urdu Jalandhry).

Guarantees theological correctness:
- Surah 1: Ayah 1 is Bismillah.
- Surahs 2-8, 10-114: Bismillah prefix is stripped from Ayah 1 (handles standard and shaddah prefixes).
- Surah 9: No Bismillah.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import delete, select, func
from app.core.config import settings
from app.core.database import async_session_factory, init_db, close_db
from app.models import Surah, Ayah, Translation

# Bismillah prefixes in Uthmani script (including shaddah variant on Ba in 95:1 and 97:1)
UTHMANI_BISMILLAH_STANDARD = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ "
UTHMANI_BISMILLAH_SHADDAH = "بِّسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ "
SIMPLE_BISMILLAH = "بسم الله الرحمن الرحيم "


def load_surah_metadata() -> dict:
    meta_path = settings.DATA_DIR / settings.SURAH_METADATA_FILE
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file missing at {meta_path}. Run prepare_metadata.py first.")
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_tanzil_file(path: Path) -> List[Tuple[int, int, str]]:
    if not path.exists():
        raise FileNotFoundError(f"File missing at {path}. Run download_data.py first.")
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                parts = stripped.split("|")
                if len(parts) >= 3:
                    records.append((int(parts[0]), int(parts[1]), parts[2]))
    if len(records) != 6236:
        raise ValueError(f"Expected 6236 verses in {path.name}, got {len(records)}")
    return records


async def seed_database() -> None:
    start_time = time.perf_counter()
    print("==================================================================")
    print("          WIRD ENGINE: DATABASE SEEDING & INGESTION PIPELINE      ")
    print("==================================================================")

    # 1. Initialize Tables
    print("[1/5] Initializing database schema...")
    await init_db()

    # 2. Load Metadata and Raw Files
    print("[2/5] Loading canonical metadata and text files...")
    meta = load_surah_metadata()
    surahs_meta = meta["surahs"]
    sajdas_map = {(s["sura"], s["aya"]): s["type"] for s in meta["sajdas"]}
    pages_index = meta["pages_index"]
    juzs_index = meta["juzs_index"]
    manzils_index = meta["manzils_index"]
    hizbs_index = meta["hizb_quarters_index"]

    raw_dir = settings.RAW_DATA_DIR
    uthmani_records = read_tanzil_file(raw_dir / settings.TANZIL_UTHMANI_FILE)
    simple_records = read_tanzil_file(raw_dir / settings.TANZIL_SIMPLE_FILE)
    en_records = read_tanzil_file(raw_dir / settings.TANZIL_EN_SAHIH_FILE)
    ur_records = read_tanzil_file(raw_dir / settings.TANZIL_UR_JALANDHRY_FILE)

    def get_page(sura: int, aya: int) -> int:
        curr = 1
        for p in pages_index:
            if (p["sura"] < sura) or (p["sura"] == sura and p["aya"] <= aya):
                curr = p["page"]
            else:
                break
        return curr

    def get_juz(sura: int, aya: int) -> int:
        curr = 1
        for j in juzs_index:
            if (j["sura"] < sura) or (j["sura"] == sura and j["aya"] <= aya):
                curr = j["juz"]
            else:
                break
        return curr

    def get_manzil(sura: int, aya: int) -> int:
        curr = 1
        for m in manzils_index:
            if (m["sura"] < sura) or (m["sura"] == sura and m["aya"] <= aya):
                curr = m["manzil"]
            else:
                break
        return curr

    def get_hizb(sura: int, aya: int) -> int:
        curr = 1
        for h in hizbs_index:
            if (h["sura"] < sura) or (h["sura"] == sura and h["aya"] <= aya):
                curr = h["quarter"]
            else:
                break
        return curr

    # 3. Prepare Model Instances
    print("[3/5] Processing Bismillah rules and preparing database entities...")

    # Surahs
    surah_objects = []
    for s in surahs_meta:
        surah_objects.append(
            Surah(
                id=s["id"],
                name_ar=s["name_ar"],
                name_en=s["name_en"],
                name_transliteration=s["name_transliteration"],
                revelation_place=s["revelation_place"],
                revelation_order=s["revelation_order"],
                total_ayahs=s["total_ayahs"],
                has_bismillah=s["has_bismillah"],
                start_page=s["start_page"],
                start_juz=s["start_juz"],
            )
        )

    # Ayahs
    ayah_objects = []
    translation_objects = []

    for idx in range(6236):
        u_sura, u_aya, u_text = uthmani_records[idx]
        s_sura, s_aya, s_text = simple_records[idx]
        en_sura, en_aya, en_text = en_records[idx]
        ur_sura, ur_aya, ur_text = ur_records[idx]

        assert u_sura == s_sura == en_sura == ur_sura, f"Surah mismatch at index {idx}"
        assert u_aya == s_aya == en_aya == ur_aya, f"Ayah mismatch at index {idx}"

        # Theological Bismillah handling
        clean_u_text = u_text
        clean_s_text = s_text

        if u_aya == 1 and u_sura not in (1, 9):
            # Strip preamble Bismillah for Surahs 2-8 and 10-114
            if clean_u_text.startswith(UTHMANI_BISMILLAH_STANDARD):
                clean_u_text = clean_u_text[len(UTHMANI_BISMILLAH_STANDARD):]
            elif clean_u_text.startswith(UTHMANI_BISMILLAH_SHADDAH):
                clean_u_text = clean_u_text[len(UTHMANI_BISMILLAH_SHADDAH):]

            if clean_s_text.startswith(SIMPLE_BISMILLAH):
                clean_s_text = clean_s_text[len(SIMPLE_BISMILLAH):]

        ayah_id = idx + 1
        page_num = get_page(u_sura, u_aya)
        juz_num = get_juz(u_sura, u_aya)
        manzil_num = get_manzil(u_sura, u_aya)
        hizb_num = get_hizb(u_sura, u_aya)
        sajda_val = (u_sura, u_aya) in sajdas_map
        sajda_type_val = sajdas_map.get((u_sura, u_aya))

        ayah_objects.append(
            Ayah(
                id=ayah_id,
                surah_id=u_sura,
                ayah_number=u_aya,
                text_uthmani=clean_u_text,
                text_simple=clean_s_text,
                juz=juz_num,
                manzil=manzil_num,
                page=page_num,
                hizb_quarter=hizb_num,
                sajdah=sajda_val,
                sajdah_type=sajda_type_val,
            )
        )

        # English translation
        translation_objects.append(
            Translation(
                ayah_id=ayah_id,
                surah_id=u_sura,
                ayah_number=u_aya,
                language_code="en",
                translator_id="sahih",
                text=en_text,
            )
        )

        # Urdu translation
        translation_objects.append(
            Translation(
                ayah_id=ayah_id,
                surah_id=u_sura,
                ayah_number=u_aya,
                language_code="ur",
                translator_id="jalandhry",
                text=ur_text,
            )
        )

    # 4. Perform Transactional Ingestion
    print("[4/5] Executing database batch insertion transaction...")
    async with async_session_factory() as session:
        # Clear existing rows (idempotency)
        await session.execute(delete(Translation))
        await session.execute(delete(Ayah))
        await session.execute(delete(Surah))

        # Add all entities
        session.add_all(surah_objects)
        session.add_all(ayah_objects)
        session.add_all(translation_objects)

        await session.commit()

    # 5. Verify Inserted Counts
    print("[5/5] Auditing database counts post-commit...")
    async with async_session_factory() as session:
        surah_count = (await session.execute(select(func.count(Surah.id)))).scalar_one()
        ayah_count = (await session.execute(select(func.count(Ayah.id)))).scalar_one()
        trans_count = (await session.execute(select(func.count(Translation.id)))).scalar_one()

    elapsed = time.perf_counter() - start_time
    print("==================================================================")
    print(f">> INGESTION COMPLETE in {elapsed:.2f} seconds <<")
    print(f"  Surahs Ingested:       {surah_count} (Expected: 114)")
    print(f"  Ayahs Ingested:        {ayah_count} (Expected: 6,236)")
    print(f"  Translations Ingested: {trans_count} (Expected: 12,472)")
    print("==================================================================")

    assert surah_count == 114, f"Surah count mismatch: {surah_count}"
    assert ayah_count == 6236, f"Ayah count mismatch: {ayah_count}"
    assert trans_count == 12472, f"Translation count mismatch: {trans_count}"
    print(">> INTEGRITY AUDIT: 100% PASSED <<")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed_database())
