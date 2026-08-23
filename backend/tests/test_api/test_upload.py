import io
import pytest


@pytest.mark.asyncio
async def test_upload_no_shop(client):
    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    resp = await client.post(
        "/api/v1/upload/nonexistent",
        files={"files": ("test.png", fake_image, "image/png")},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_empty_files(client):
    create_resp = await client.post(
        "/api/v1/shop",
        json={"shop_name": "Upload Shop", "device_id": "dev-upload"},
    )
    shop_id = create_resp.json()["shop_id"]

    resp = await client.post(f"/api/v1/upload/{shop_id}")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_job_not_found(client):
    resp = await client.get("/api/v1/jobs/nonexistent")
    assert resp.status_code == 404
