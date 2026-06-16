import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest

from app.main import parse_items_args


def test_parse_items_args_simple():
    s = "Mojito:2, Eau plate:1"
    items = parse_items_args(s)
    assert isinstance(items, list)
    assert items[0]["name"] == "Mojito"
    assert items[0]["quantity"] == 2
    assert items[1]["name"] == "Eau plate"
    assert items[1]["quantity"] == 1


@pytest.mark.timeout(10)
def test_server_endpoints_create_modify_cancel_and_stock(tmp_path):
    # Start server subprocess on an ephemeral port
    port = 8123
    cmd = [
        sys.executable,
        "-m",
        "app.main",
        "serve",
        f"127.0.0.1:{port}",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        # wait for server to boot
        time.sleep(0.8)

        def http_get(path):
            url = f"http://127.0.0.1:{port}{path}"
            with urllib.request.urlopen(url) as resp:
                return resp.read(), resp.getcode()

        def http_post(path, data):
            url = f"http://127.0.0.1:{port}{path}"
            body = json.dumps(data).encode()
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req) as resp:
                return resp.read(), resp.getcode()

        # Check stock listing
        body, code = http_get("/api/stock")
        assert code == 200
        stock = json.loads(body)
        assert "Mojito" in stock

        # Create order
        order_payload = {"festivalier_id": "tester", "items": [{"name": "Mojito", "quantity": 1}]}
        body, code = http_post("/api/order", order_payload)
        assert code == 201
        created = json.loads(body)
        oid = created.get("id")
        assert oid is not None

        # List orders
        body, code = http_get("/api/orders")
        assert code == 200
        orders = json.loads(body)
        assert any(o["id"] == oid for o in orders)

        # Modify order
        modify_payload = {"items": [{"name": "Mojito", "quantity": 2}, {"name": "Eau plate", "quantity": 1}]}
        body, code = http_post(f"/api/order/{oid}/modify", modify_payload)
        assert code == 200

        # Cancel order
        body, code = http_post(f"/api/order/{oid}/status", {"status": "ANNULE"})
        assert code == 200

        # Check order status
        body, code = http_get(f"/api/order/{oid}")
        assert code == 200
        order = json.loads(body)
        assert order.get("status") == "ANNULE"

        # Set stock item
        body, code = http_post("/api/stock/Mojito", {"quantity": 50})
        assert code == 200
        body, code = http_get("/api/stock/Mojito")
        assert code == 200
        item = json.loads(body)
        assert item.get("quantity") == 50

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
        # consume outputs to avoid resource warnings
        try:
            proc.communicate(timeout=1)
        except Exception:
            pass
    