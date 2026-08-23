import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "runova-print"


@pytest.mark.asyncio
async def test_create_shop(client):
    resp = await client.post(
        "/api/v1/shop",
        json={"shop_name": "Test Shop", "device_id": "test-device-001"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["shop_name"] == "Test Shop"
    assert "shop_id" in data


@pytest.mark.asyncio
async def test_get_shop(client):
    create_resp = await client.post(
        "/api/v1/shop",
        json={"shop_name": "My Shop", "device_id": "dev-123"},
    )
    shop_id = create_resp.json()["shop_id"]

    resp = await client.get(f"/api/v1/shop/{shop_id}")
    assert resp.status_code == 200
    assert resp.json()["shop_name"] == "My Shop"


@pytest.mark.asyncio
async def test_get_shop_not_found(client):
    resp = await client.get("/api/v1/shop/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_pending_jobs(client):
    create_resp = await client.post(
        "/api/v1/shop",
        json={"shop_name": "Pending Shop", "device_id": "dev-pending"},
    )
    shop_id = create_resp.json()["shop_id"]

    resp = await client.get(f"/api/v1/shop/{shop_id}/pending")
    assert resp.status_code == 200
    assert "jobs" in resp.json()
