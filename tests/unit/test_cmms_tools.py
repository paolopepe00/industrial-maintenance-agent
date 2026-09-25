from unittest.mock import patch, Mock
from src.tools.cmms import get_sensor_data, create_work_order


def test_get_sensor_data_success():
    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "machine_id": "P-102",
        "vibration_rms_mm_s": 6.8,
        "vibration_dominant_freq": "2x_running_speed",
    }

    with patch("src.tools.cmms.requests.get", return_value=fake_response) as mock_get:
        result = get_sensor_data.invoke({"machine_id": "P-102"})

    mock_get.assert_called_once_with("http://localhost:8001/machines/P-102/sensors")
    assert result["vibration_rms_mm_s"] == 6.8
    assert result["vibration_dominant_freq"] == "2x_running_speed"


def test_get_sensor_data_machine_not_found():
    fake_response = Mock()
    fake_response.status_code = 404
    fake_response.json.return_value = {"detail": "Machine X-999 not found"}

    with patch("src.tools.cmms.requests.get", return_value=fake_response):
        result = get_sensor_data.invoke({"machine_id": "X-999"})

    assert "error" in result
    assert "not found" in result["error"]


def test_create_work_order_calls_correct_endpoint():
    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"work_order_id": "WO-TEST01", "status": "open"}

    with patch("src.tools.cmms.requests.post", return_value=fake_response) as mock_post:
        result = create_work_order.invoke({"machine_id": "P-102", "description": "Test issue"})

    mock_post.assert_called_once_with(
        "http://localhost:8001/work-orders",
        params={"machine_id": "P-102", "description": "Test issue"},
    )
    assert result["work_order_id"] == "WO-TEST01"