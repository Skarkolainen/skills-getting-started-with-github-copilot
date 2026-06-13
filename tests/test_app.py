import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    baseline = copy.deepcopy(app_module.activities)
    app_module.activities = copy.deepcopy(baseline)
    yield
    app_module.activities = copy.deepcopy(baseline)


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_seeded_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_successfully_adds_participant(client):
    email = "new.student@mergington.edu"

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post("/activities/Unknown Club/signup", params={"email": "a@b.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_duplicate_signup(client):
    existing_email = app_module.activities["Chess Club"]["participants"][0]

    response = client.post("/activities/Chess Club/signup", params={"email": existing_email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_returns_400_when_activity_is_full(client):
    app_module.activities["Chess Club"]["participants"] = [
        f"student{i}@mergington.edu"
        for i in range(app_module.activities["Chess Club"]["max_participants"])
    ]

    response = client.post("/activities/Chess Club/signup", params={"email": "overflow@mergington.edu"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_successfully_removes_participant(client):
    email = app_module.activities["Chess Club"]["participants"][0]

    response = client.delete("/activities/Chess Club/participants", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from Chess Club"
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete("/activities/Unknown Club/participants", params={"email": "a@b.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_student_not_signed_up(client):
    response = client.delete("/activities/Chess Club/participants", params={"email": "not.signed@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"