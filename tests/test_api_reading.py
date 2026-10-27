"""Comprehensive API integration and latency tests for Quran Reading endpoints."""

import time
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_surahs_returns_114(client: AsyncClient):
    """Assert GET /api/v1/surahs returns all 114 Surahs with 200 OK."""
    response = await client.get("/api/v1/surahs")
    assert response.status_code == 200
    surahs = response.json()
    assert len(surahs) == 114
    assert surahs[0]["id"] == 1
    assert surahs[0]["name_en"] == "Al-Faatiha"
    assert surahs[113]["id"] == 114
    assert surahs[113]["name_en"] == "An-Naas"


@pytest.mark.asyncio
async def test_surah_1_fatihah_reading(client: AsyncClient):
    """Assert Surah 1 has 7 ayahs, Ayah 1 is Bismillah, and both translations load."""
    response = await client.get("/api/v1/surahs/1?translations=en,ur")
    assert response.status_code == 200
    data = response.json()
    assert data["surah"]["id"] == 1
    assert data["total_ayahs"] == 7
    assert len(data["ayahs"]) == 7
    assert data["ayahs"][0]["ayah_number"] == 1
    assert "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ" in data["ayahs"][0]["text_uthmani"]
    assert "en" in data["ayahs"][0]["translations"]
    assert "ur" in data["ayahs"][0]["translations"]


@pytest.mark.asyncio
async def test_surah_2_baqarah_stripped_bismillah(client: AsyncClient):
    """Assert Surah 2 has 286 ayahs and Ayah 1 has Bismillah cleanly stripped."""
    response = await client.get("/api/v1/surahs/2?translations=en")
    assert response.status_code == 200
    data = response.json()
    assert data["surah"]["id"] == 2
    assert data["total_ayahs"] == 286
    assert len(data["ayahs"]) == 286
    assert data["ayahs"][0]["text_uthmani"] == "الٓمٓ"
    assert data["ayahs"][0]["text_simple"] == "الم"
    assert "en" in data["ayahs"][0]["translations"]
    assert "ur" not in data["ayahs"][0]["translations"]


@pytest.mark.asyncio
async def test_surah_9_has_bismillah_false(client: AsyncClient):
    """Assert Surah 9 (At-Tawbah) has has_bismillah = False and 129 ayahs."""
    response = await client.get("/api/v1/surahs/9")
    assert response.status_code == 200
    data = response.json()
    assert data["surah"]["id"] == 9
    assert data["surah"]["has_bismillah"] is False
    assert data["total_ayahs"] == 129


@pytest.mark.asyncio
async def test_ayah_2_255_ayatul_kursi(client: AsyncClient):
    """Assert Ayatul Kursi (2:255) returns accurate verse and boundary metadata."""
    response = await client.get("/api/v1/ayahs/2/255?translations=en,ur")
    assert response.status_code == 200
    ayah = response.json()
    assert ayah["surah_id"] == 2
    assert ayah["ayah_number"] == 255
    assert ayah["page"] == 42
    assert ayah["juz"] == 3
    assert ayah["manzil"] == 1
    assert "Allah" in ayah["translations"]["en"]
    assert len(ayah["translations"]["ur"]) > 50


@pytest.mark.asyncio
async def test_juz_catalog_and_juz_reading(client: AsyncClient):
    """Assert /juz returns 30 juzs and /juz/30 returns 564 ayahs."""
    r_list = await client.get("/api/v1/juz")
    assert r_list.status_code == 200
    juzs = r_list.json()
    assert len(juzs) == 30

    r_juz30 = await client.get("/api/v1/juz/30?translations=en")
    assert r_juz30.status_code == 200
    juz30 = r_juz30.json()
    assert juz30["juz"]["juz_number"] == 30
    assert juz30["total_ayahs"] == 564
    assert len(juz30["ayahs"]) == 564


@pytest.mark.asyncio
async def test_404_error_handling(client: AsyncClient):
    """Assert invalid IDs return 404 with structured error envelope."""
    r = await client.get("/api/v1/surahs/999")
    assert r.status_code == 404
    assert r.json()["error"] is True

    r = await client.get("/api/v1/ayahs/1/999")
    assert r.status_code == 404
    assert r.json()["error"] is True

    r = await client.get("/api/v1/juz/999")
    assert r.status_code == 404
    assert r.json()["error"] is True


@pytest.mark.asyncio
async def test_endpoint_latency_benchmark(client: AsyncClient):
    """Benchmark: Assert read endpoints execute well under 15ms target."""
    await client.get("/api/v1/surahs")

    t0 = time.perf_counter()
    r = await client.get("/api/v1/surahs")
    t_surahs = (time.perf_counter() - t0) * 1000
    assert r.status_code == 200
    assert t_surahs < 15.0, f"Latency {t_surahs:.2f}ms exceeds 15ms"

    t0 = time.perf_counter()
    r = await client.get("/api/v1/surahs/2?translations=en,ur")
    t_reading = (time.perf_counter() - t0) * 1000
    assert r.status_code == 200
    assert t_reading < 15.0, f"Latency {t_reading:.2f}ms exceeds 15ms"
