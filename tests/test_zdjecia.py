"""Zdjęcia z miasta: GPS z EXIF → najbliższy kosz (do 80 m), paczka wielu plików."""
import io
from unittest.mock import patch

import pytest
from PIL import Image
from PIL.TiffImagePlugin import IFDRational

from app import clock, photos
from app.models import Point
from app.osm_import import import_points


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def jpeg_with_gps(lat, lon):
    """JPEG 32×32 z GPSInfo w EXIF (tak zapisuje aparat telefonu z włączoną lokalizacją)."""
    dms = lambda v: (IFDRational(int(v)), IFDRational(int(v * 60 % 60)), IFDRational(int(round(v * 3600 % 60 * 100)), 100))
    exif = Image.Exif()
    exif[0x8825] = {1: "N" if lat >= 0 else "S", 2: dms(abs(lat)), 3: "E" if lon >= 0 else "W", 4: dms(abs(lon))}
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (120, 120, 120)).save(buf, "JPEG", exif=exif.tobytes())
    return buf.getvalue()


def test_gps_from_exif_roundtrip():
    lat, lon = photos.gps_from_exif(jpeg_with_gps(50.0618, 19.9360))
    assert abs(lat - 50.0618) < 1e-3 and abs(lon - 19.9360) < 1e-3
    buf = io.BytesIO(); Image.new("RGB", (8, 8)).save(buf, "JPEG")
    assert photos.gps_from_exif(buf.getvalue()) is None


def test_batch_upload_matches_nearest_bin_by_exif(client, demo, staff):
    p = Point.query.filter_by(kind="bin").first()
    far_lat = p.lat + 0.02  # ~2 km dalej: brak kosza w 80 m
    data = {"photos": [(io.BytesIO(jpeg_with_gps(p.lat, p.lon)), "a.jpg"), (io.BytesIO(jpeg_with_gps(far_lat, p.lon)), "b.jpg"),
                       (io.BytesIO(b"\xff\xd8\xff\xe0" + b"0" * 64), "c.jpg")]}
    with patch.object(photos, "analyze_in_background"):
        r = client.post("/api/photo", data=data, content_type="multipart/form-data")
    assert r.status_code == 200
    a, b, c = r.json["results"]
    assert a["ok"] and a["point_id"] == p.id and a["matched_by"] == "exif" and a["distance_m"] <= photos.MATCH_M
    assert not b["ok"] and "limit 80 m" in b["message"]
    assert not c["ok"]


def test_single_upload_without_gps_needs_point(client, demo, staff):
    buf = io.BytesIO(); Image.new("RGB", (8, 8)).save(buf, "JPEG")
    r = client.post("/api/photo", data={"photo": (io.BytesIO(buf.getvalue()), "x.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 400 and "wskaż kosz" in r.json["message"]
    assert client.get("/zdjecia").status_code == 200
