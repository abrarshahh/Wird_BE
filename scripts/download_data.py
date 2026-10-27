"""Automated downloader for canonical Tanzil Quranic texts and translations.

Downloads:
1. Uthmani Quran Text (Madinah Mushaf script with pause marks and sajdah signs)
2. Simple Clean Quran Text (Clean Arabic without diacritics for search indexing)
3. English Translation (Saheeh International)
4. Urdu Translation (Fateh Muhammad Jalandhry)
5. Canonical Quran Metadata XML (Structure, boundaries, pages, sajdas)
"""

import argparse
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings

# HTTP Request headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://tanzil.net/download/",
}

TOTAL_EXPECTED_AYAHS = 6236


def count_verse_lines(filepath: Path) -> int:
    """Count non-comment, valid verse data lines in a Tanzil text file."""
    if not filepath.exists() or filepath.stat().st_size == 0:
        return 0
    count = 0
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                parts = stripped.split("|")
                if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
                    count += 1
    return count


def verify_xml_file(filepath: Path) -> bool:
    """Verify that the XML file is well-formed and contains suras."""
    if not filepath.exists() or filepath.stat().st_size == 0:
        return False
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        suras = root.findall(".//sura")
        return len(suras) == 114
    except Exception:
        return False


def download_file_with_retry(
    url: str,
    target_path: Path,
    expected_verses: int = TOTAL_EXPECTED_AYAHS,
    is_xml: bool = False,
    force: bool = False,
    max_retries: int = 3,
) -> bool:
    """Download a canonical dataset with retry logic and integrity verification."""
    # Check if already downloaded and valid
    if not force and target_path.exists():
        if is_xml and verify_xml_file(target_path):
            print(f"[CACHE] {target_path.name} already exists and is valid (114 Surahs). Skipping.")
            return True
        elif not is_xml:
            existing_count = count_verse_lines(target_path)
            if existing_count == expected_verses:
                size_kb = target_path.stat().st_size / 1024
                print(f"[CACHE] {target_path.name} ({size_kb:.1f} KB) verified with {existing_count} verses. Skipping.")
                return True

    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(".tmp")

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[DOWNLOADING] Attempt {attempt}/{max_retries} -> {target_path.name} from {url[:70]}...")
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()

            with open(temp_path, "wb") as f:
                f.write(content)

            # Integrity verification
            if is_xml:
                if verify_xml_file(temp_path):
                    temp_path.replace(target_path)
                    size_kb = target_path.stat().st_size / 1024
                    print(f"[SUCCESS] {target_path.name} downloaded ({size_kb:.1f} KB, 114 Surahs verified).")
                    return True
                else:
                    print(f"[ERROR] {target_path.name} XML verification failed.")
            else:
                verse_count = count_verse_lines(temp_path)
                if verse_count == expected_verses:
                    temp_path.replace(target_path)
                    size_kb = target_path.stat().st_size / 1024
                    print(f"[SUCCESS] {target_path.name} downloaded ({size_kb:.1f} KB, {verse_count} verses verified).")
                    return True
                else:
                    print(f"[ERROR] {target_path.name} verse count mismatch: expected {expected_verses}, got {verse_count}.")

        except (urllib.error.URLError, TimeoutError, Exception) as e:
            print(f"[RETRY] Error downloading {target_path.name}: {e}")

        if temp_path.exists():
            temp_path.unlink()

        if attempt < max_retries:
            backoff = attempt * 2
            print(f"Waiting {backoff}s before retrying...")
            time.sleep(backoff)

    print(f"[FAILED] Could not download and verify {target_path.name} after {max_retries} attempts.")
    return False


def main() -> int:
    """Main entrypoint for dataset acquisition."""
    parser = argparse.ArgumentParser(description="Download canonical Tanzil Quranic data.")
    parser.add_argument("--force", action="store_true", help="Force re-download of existing files")
    args = parser.parse_args()

    raw_dir = settings.RAW_DATA_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("==================================================================")
    print("      WIRD ENGINE: CANONICAL QURAN DATA ACQUISITION PIPELINE      ")
    print("==================================================================")
    print(f"Target Directory: {raw_dir}")
    print(f"Force Mode:       {args.force}\n")

    downloads = [
        {
            "name": "1. Uthmani Quran Text",
            "url": settings.URL_TANZIL_UTHMANI,
            "path": raw_dir / settings.TANZIL_UTHMANI_FILE,
            "is_xml": False,
        },
        {
            "name": "2. Simple Clean Quran Text",
            "url": settings.URL_TANZIL_SIMPLE,
            "path": raw_dir / settings.TANZIL_SIMPLE_FILE,
            "is_xml": False,
        },
        {
            "name": "3. English Translation (Saheeh Int.)",
            "url": settings.URL_TANZIL_EN_SAHIH,
            "path": raw_dir / settings.TANZIL_EN_SAHIH_FILE,
            "is_xml": False,
        },
        {
            "name": "4. Urdu Translation (Jalandhry)",
            "url": settings.URL_TANZIL_UR_JALANDHRY,
            "path": raw_dir / settings.TANZIL_UR_JALANDHRY_FILE,
            "is_xml": False,
        },
        {
            "name": "5. Quran Canonical Metadata (XML)",
            "url": settings.URL_TANZIL_METADATA_XML,
            "path": raw_dir / settings.TANZIL_METADATA_XML_FILE,
            "is_xml": True,
        },
    ]

    all_success = True
    for item in downloads:
        print(f"--- {item['name']} ---")
        success = download_file_with_retry(
            url=item["url"],
            target_path=item["path"],
            is_xml=item["is_xml"],
            force=args.force,
        )
        if not success:
            all_success = False
        print()

    print("==================================================================")
    print("                     INTEGRITY AUDIT SUMMARY                     ")
    print("==================================================================")

    audit_passed = True
    for item in downloads:
        path = item["path"]
        if not path.exists():
            print(f"[FAIL] {path.name:22} | File missing")
            audit_passed = False
            continue

        size_kb = path.stat().st_size / 1024
        if item["is_xml"]:
            valid = verify_xml_file(path)
            status = "PASS (114 Surahs)" if valid else "FAIL (Invalid XML)"
            if not valid:
                audit_passed = False
            print(f"[OK]   {path.name:22} | {size_kb:8.1f} KB | {status}")
        else:
            verses = count_verse_lines(path)
            valid = verses == TOTAL_EXPECTED_AYAHS
            status = f"PASS ({verses} verses)" if valid else f"FAIL ({verses} verses)"
            if not valid:
                audit_passed = False
            print(f"[OK]   {path.name:22} | {size_kb:8.1f} KB | {status}")

    print("==================================================================")
    if all_success and audit_passed:
        print(">> ALL CANONICAL DATASETS SUCCESSFULLY ACQUIRED & VERIFIED (6,236 Verses) <<")
        return 0
    else:
        print(">> DATASET ACQUISITION ENCOUNTERED FAILURES <<")
        return 1


if __name__ == "__main__":
    sys.exit(main())
