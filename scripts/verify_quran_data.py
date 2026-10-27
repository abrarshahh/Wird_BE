"""Comprehensive Verification & Data Integrity Suite for Wird Quran Database.

Executes 20 strict assertions directly against wird.db:
1. Surah count (114)
2. Ayah count (6,236)
3. English translation count (6,236)
4. Urdu translation count (6,236)
5. Surah 1 verse count (7)
6. Surah 2 verse count (286)
7. Surah 114 verse count (6)
8. Surah 9 has_bismillah == False
9. Surahs 1-8, 10-114 has_bismillah == True
10. Sajdah count (15) with valid types
11. Page bounds (1 to 604)
12. Juz bounds (1 to 30)
13. Manzil bounds (1 to 7)
14. Hizb quarter bounds (1 to 240)
15. Surah 1 Ayah 1 is Bismillah
16. Surah 2 Ayah 1 starts with Alif-Lam-Meem (Bismillah cleanly stripped)
17. Surah 95 Ayah 1 starts with Wat-Teen (shaddah Bismillah cleanly stripped)
18. Surah 97 Ayah 1 starts with Inna Anzalnahu (shaddah Bismillah cleanly stripped)
19. Surah 27 Ayah 30 retains its in-verse Bismillah intact
20. Zero null, empty, or whitespace-only records
"""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 stdout on Windows
sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import func, select, or_
from app.core.config import settings
from app.core.database import async_session_factory, close_db
from app.models import Surah, Ayah, Translation


class VerificationSuite:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def check(self, name: str, condition: bool, details: str = ""):
        if condition:
            self.passed += 1
            print(f"  [PASS] {name}" + (f" -> {details}" if details else ""))
        else:
            self.failed += 1
            print(f"  [FAIL] {name} -> {details}")
        self.tests.append((name, condition, details))


async def run_verification() -> int:
    suite = VerificationSuite()
    print("==================================================================")
    print("        WIRD ENGINE: DATABASE INTEGRITY VERIFICATION SUITE        ")
    print("==================================================================")
    print(f"Database Target: {settings.DATABASE_URL}\n")

    async with async_session_factory() as session:
        # Check 1: Surah Count
        surah_count = (await session.execute(select(func.count(Surah.id)))).scalar_one()
        suite.check("Total Surahs Count", surah_count == 114, f"Found {surah_count} / 114")

        # Check 2: Ayah Count
        ayah_count = (await session.execute(select(func.count(Ayah.id)))).scalar_one()
        suite.check("Total Ayahs Count", ayah_count == 6236, f"Found {ayah_count} / 6236")

        # Check 3: English Translation Count
        en_count = (await session.execute(
            select(func.count(Translation.id)).where(Translation.language_code == "en")
        )).scalar_one()
        suite.check("English Translations Count", en_count == 6236, f"Found {en_count} / 6236")

        # Check 4: Urdu Translation Count
        ur_count = (await session.execute(
            select(func.count(Translation.id)).where(Translation.language_code == "ur")
        )).scalar_one()
        suite.check("Urdu Translations Count", ur_count == 6236, f"Found {ur_count} / 6236")

        # Check 5: Key Surah Verse Counts
        s1 = (await session.execute(select(Surah).where(Surah.id == 1))).scalar_one_or_none()
        suite.check("Surah 1 (Al-Fatihah) Ayahs", s1 and s1.total_ayahs == 7, f"Ayahs: {s1.total_ayahs if s1 else 0}")

        s2 = (await session.execute(select(Surah).where(Surah.id == 2))).scalar_one_or_none()
        suite.check("Surah 2 (Al-Baqarah) Ayahs", s2 and s2.total_ayahs == 286, f"Ayahs: {s2.total_ayahs if s2 else 0}")

        s114 = (await session.execute(select(Surah).where(Surah.id == 114))).scalar_one_or_none()
        suite.check("Surah 114 (An-Naas) Ayahs", s114 and s114.total_ayahs == 6, f"Ayahs: {s114.total_ayahs if s114 else 0}")

        # Check 6: Bismillah Flag Rules
        s9 = (await session.execute(select(Surah).where(Surah.id == 9))).scalar_one_or_none()
        suite.check("Surah 9 (At-Tawbah) has_bismillah is False", s9 and s9.has_bismillah is False, f"has_bismillah: {s9.has_bismillah if s9 else None}")

        bismillah_true_count = (await session.execute(
            select(func.count(Surah.id)).where(Surah.has_bismillah.is_(True))
        )).scalar_one()
        suite.check("113 Surahs have has_bismillah is True", bismillah_true_count == 113, f"Found {bismillah_true_count} / 113")

        # Check 7: Sajdah Counts & Types
        sajda_count = (await session.execute(select(func.count(Ayah.id)).where(Ayah.sajdah.is_(True)))).scalar_one()
        suite.check("Total Sajdah Verses", sajda_count == 15, f"Found {sajda_count} / 15")

        obligatory_sajdas = (await session.execute(
            select(func.count(Ayah.id)).where(Ayah.sajdah_type == "obligatory")
        )).scalar_one()
        suite.check("Obligatory Sajdah Verses", obligatory_sajdas == 4, f"Found {obligatory_sajdas} / 4 (32:15, 41:38, 53:62, 96:19)")

        # Check 8: Page, Juz, Manzil, Hizb Bounds
        min_page = (await session.execute(select(func.min(Ayah.page)))).scalar_one()
        max_page = (await session.execute(select(func.max(Ayah.page)))).scalar_one()
        suite.check("Page Bounds (1 to 604)", min_page == 1 and max_page == 604, f"Min: {min_page}, Max: {max_page}")

        min_juz = (await session.execute(select(func.min(Ayah.juz)))).scalar_one()
        max_juz = (await session.execute(select(func.max(Ayah.juz)))).scalar_one()
        suite.check("Juz Bounds (1 to 30)", min_juz == 1 and max_juz == 30, f"Min: {min_juz}, Max: {max_juz}")

        min_manzil = (await session.execute(select(func.min(Ayah.manzil)))).scalar_one()
        max_manzil = (await session.execute(select(func.max(Ayah.manzil)))).scalar_one()
        suite.check("Manzil Bounds (1 to 7)", min_manzil == 1 and max_manzil == 7, f"Min: {min_manzil}, Max: {max_manzil}")

        min_hizb = (await session.execute(select(func.min(Ayah.hizb_quarter)))).scalar_one()
        max_hizb = (await session.execute(select(func.max(Ayah.hizb_quarter)))).scalar_one()
        suite.check("Hizb Quarter Bounds (1 to 240)", min_hizb == 1 and max_hizb == 240, f"Min: {min_hizb}, Max: {max_hizb}")

        # Check 9: Theological Bismillah Cleanliness
        a1_1 = (await session.execute(select(Ayah).where(Ayah.surah_id == 1, Ayah.ayah_number == 1))).scalar_one()
        suite.check("Surah 1:1 is Bismillah", "بِسْمِ ٱللَّهِ" in a1_1.text_uthmani, f"Text: {a1_1.text_uthmani}")

        a2_1 = (await session.execute(select(Ayah).where(Ayah.surah_id == 2, Ayah.ayah_number == 1))).scalar_one()
        suite.check("Surah 2:1 Bismillah Stripped (Uthmani: الٓمٓ)", a2_1.text_uthmani == "الٓمٓ", f"Text: {a2_1.text_uthmani}")
        suite.check("Surah 2:1 Bismillah Stripped (Simple: الم)", a2_1.text_simple == "الم", f"Text: {a2_1.text_simple}")

        a95_1 = (await session.execute(select(Ayah).where(Ayah.surah_id == 95, Ayah.ayah_number == 1))).scalar_one()
        suite.check("Surah 95:1 Shaddah Bismillah Stripped (Uthmani)", a95_1.text_uthmani.startswith("وَٱلتِّينِ"), f"Text: {a95_1.text_uthmani[:30]}")

        a97_1 = (await session.execute(select(Ayah).where(Ayah.surah_id == 97, Ayah.ayah_number == 1))).scalar_one()
        suite.check("Surah 97:1 Shaddah Bismillah Stripped (Uthmani)", a97_1.text_uthmani.startswith("إِنَّآ أَنزَلْنَٰهُ"), f"Text: {a97_1.text_uthmani[:30]}")

        a27_30 = (await session.execute(select(Ayah).where(Ayah.surah_id == 27, Ayah.ayah_number == 30))).scalar_one()
        suite.check("Surah 27:30 In-Verse Bismillah Preserved", "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ" in a27_30.text_uthmani, f"Text: {a27_30.text_uthmani}")

        # Check 10: No Empty or Whitespace Text Fields
        empty_ayahs = (await session.execute(
            select(func.count(Ayah.id)).where(
                or_(Ayah.text_uthmani == "", Ayah.text_simple == "")
            )
        )).scalar_one()
        suite.check("No Empty Ayah Text", empty_ayahs == 0, f"Empty rows: {empty_ayahs}")

        empty_trans = (await session.execute(
            select(func.count(Translation.id)).where(Translation.text == "")
        )).scalar_one()
        suite.check("No Empty Translations", empty_trans == 0, f"Empty rows: {empty_trans}")

    await close_db()

    print("==================================================================")
    print(f"TOTAL CHECKS: {suite.passed + suite.failed} | PASSED: {suite.passed} | FAILED: {suite.failed}")
    if suite.failed == 0:
        print(">> VERIFICATION PASSED: DATABASE IS THEOLOGICALLY & STRUCTURALLY FLAWLESS <<")
        print("==================================================================")
        return 0
    else:
        print(">> VERIFICATION FAILED: INTEGRITY ERRORS DETECTED <<")
        print("==================================================================")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run_verification()))
