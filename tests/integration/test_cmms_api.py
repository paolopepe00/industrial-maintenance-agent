from fastapi.testclient import TestClient

from cmms.api.main import app

client = TestClient(app)


def test_get_machine_status():
    response = client.get("/machines/P-102")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "P-102"
    assert data["type"] == "centrifugal_pump"


def test_get_machine_not_found():
    response = client.get("/machines/NONEXISTENT")
    assert response.status_code == 404


def test_get_sensor_data():
    response = client.get("/machines/P-102/sensors")
    assert response.status_code == 200
    data = response.json()
    assert "vibration_rms_mm_s" in data


def test_create_and_retrieve_work_order():
    create_resp = client.post(
        "/work-orders",
        params={"machine_id": "P-102", "description": "pytest integration test order"},
    )
    assert create_resp.status_code == 200
    work_order_id = create_resp.json()["work_order_id"]

    list_resp = client.get("/work-orders", params={"machine_id": "P-102"})
    assert list_resp.status_code == 200
    ids = [wo["id"] for wo in list_resp.json()["open_work_orders"]]
    assert work_order_id in ids