"""Die Catch-all liefert Dateien nur aus ``static/``, sonst ``index.html`` (eedc N-744).

**Die Lage.** ``main.py::serve_spa`` setzte ``static_path / full_path`` ohne
Eingrenzung zusammen. uvicorn dekodiert ``%2e%2e`` zu ``..``, Starlettes
``{full_path:path}`` normalisiert nicht, ``FileResponse`` auch nicht — also
lieferte ``GET /%2e%2e/main.py`` den Quelltext des Servers (dieselbe Klasse
wie im Add-on, #65/F-62).

**Die Regel.** Ausgeliefert wird nur, was nach ``resolve()`` innerhalb von
``static/`` liegt und eine Datei ist; alles andere bekommt ``index.html``.

Zwei Ebenen: (a) ``TestClient`` (In-Prozess). httpx normalisiert ein
*literales* ``/../`` schon im Client weg — die Probe ``/../main.py`` erreicht
den Server als ``/main.py`` und zeigt den Defekt deshalb nicht; die kodierten
Formen ``%2e%2e`` und ``..%2f`` dagegen kommen dekodiert als ``../main.py``
bei der Route an. (b) Der echte Server unter uvicorn auf 127.0.0.1 mit
``curl --path-as-is`` — der Weg, den ein Angreifer nimmt.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
_STATIC = _BACKEND / "static"
_INDEX_KOPF = "<!doctype html>"
_QUELLTEXT_KOPF = '"""\nEEDC Community Server'

pytestmark = pytest.mark.skipif(
    not ((_STATIC / "assets").exists() and (_STATIC / "index.html").exists()),
    reason="ohne Frontend-Build ist die Catch-all nicht registriert",
)


# (a) In-Prozess ---------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    import main

    # Ohne Kontextmanager: kein Lifespan, keine Datenbank nötig.
    return TestClient(main.app)


@pytest.mark.parametrize("pfad", ["/../main.py", "/%2e%2e/main.py", "/..%2fmain.py", "/%2e%2e/core/config.py"])
def test_traversal_bekommt_index(client, pfad):
    r = client.get(pfad)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert r.text.lstrip().lower().startswith(_INDEX_KOPF)
    assert "EEDC Community Server" not in r.text


def test_datei_aus_static_wird_geliefert(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert r.text == (_STATIC / "robots.txt").read_text()


def test_unbekannter_pfad_bekommt_index(client):
    r = client.get("/irgendwas/tief")
    assert r.status_code == 200
    assert r.text.lstrip().lower().startswith(_INDEX_KOPF)


# (b) Laufzeit: uvicorn + curl --path-as-is -----------------------------------

def _freier_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _curl(port: int, pfad: str) -> tuple[str, str]:
    """``curl --path-as-is``: Statuszeile+Kopf und Rumpf getrennt."""
    out = subprocess.run(
        ["curl", "-s", "--path-as-is", "-D", "-", f"http://127.0.0.1:{port}{pfad}"],
        capture_output=True, timeout=10, check=True,
    ).stdout  # Bytes: text=True würde \r\n zu \n falten und die Trennung verlieren
    kopf, _, rumpf = out.partition(b"\r\n\r\n")
    return kopf.decode(), rumpf.decode()


@pytest.mark.skipif(shutil.which("curl") is None, reason="curl fehlt")
def test_uvicorn_path_as_is_liefert_index():
    port = _freier_port()
    env = dict(os.environ, DATABASE_URL="sqlite+aiosqlite:///:memory:", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=_BACKEND, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                if proc.poll() is not None:
                    pytest.fail("uvicorn ist beim Start beendet")
                time.sleep(0.1)
        else:
            pytest.fail("uvicorn nicht erreichbar")

        for pfad in ("/%2e%2e/main.py", "/..%2fmain.py", "/%2e%2e/core/config.py"):
            kopf, rumpf = _curl(port, pfad)
            assert kopf.startswith("HTTP/1.1 200"), (pfad, kopf)
            assert "content-type: text/html" in kopf.lower(), (pfad, kopf)
            assert rumpf.lstrip().lower().startswith(_INDEX_KOPF), (pfad, rumpf[:80])
            assert not rumpf.startswith(_QUELLTEXT_KOPF), pfad

        kopf, rumpf = _curl(port, "/robots.txt")
        assert rumpf == (_STATIC / "robots.txt").read_text()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
