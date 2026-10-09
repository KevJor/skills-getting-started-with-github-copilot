from copy import deepcopy

import pytest


ACTIVITY_NAME = "Chess Club"
SIGNUP_PATH = f"/activities/{ACTIVITY_NAME}/signup"
NEW_EMAIL = "test.student@mergington.edu"


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_current_data(client, isolated_activities):
    expected = deepcopy(isolated_activities)

    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == expected
    activity = response.json()[ACTIVITY_NAME]
    assert isinstance(activity["description"], str)
    assert isinstance(activity["schedule"], str)
    assert isinstance(activity["max_participants"], int)
    assert isinstance(activity["participants"], list)


def test_signup_adds_one_participant(client):
    expected = client.get("/activities").json()
    assert NEW_EMAIL not in expected[ACTIVITY_NAME]["participants"]
    expected[ACTIVITY_NAME]["participants"].append(NEW_EMAIL)

    response = client.post(SIGNUP_PATH, params={"email": NEW_EMAIL})

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {NEW_EMAIL} for {ACTIVITY_NAME}"
    }
    assert client.get("/activities").json() == expected


def test_signup_rejects_duplicate_without_changing_data(client):
    expected = client.get("/activities").json()
    email = expected[ACTIVITY_NAME]["participants"][0]

    response = client.post(SIGNUP_PATH, params={"email": email})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert client.get("/activities").json() == expected


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_unknown_activity_returns_not_found_without_changing_data(client, method):
    expected = client.get("/activities").json()

    response = client.request(
        method, "/activities/Unknown Activity/signup", params={"email": NEW_EMAIL}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json() == expected


def test_unregister_removes_only_requested_participant(client):
    expected = client.get("/activities").json()
    email = expected[ACTIVITY_NAME]["participants"].pop(0)

    response = client.delete(SIGNUP_PATH, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {ACTIVITY_NAME}"
    }
    assert client.get("/activities").json() == expected


def test_unregister_rejects_nonparticipant_without_changing_data(client):
    expected = client.get("/activities").json()
    assert NEW_EMAIL not in expected[ACTIVITY_NAME]["participants"]

    response = client.delete(SIGNUP_PATH, params={"email": NEW_EMAIL})

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert client.get("/activities").json() == expected


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_signup_route_requires_email_without_changing_data(client, method):
    expected = client.get("/activities").json()

    response = client.request(method, SIGNUP_PATH)

    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"]
        for error in response.json()["detail"]
    )
    assert client.get("/activities").json() == expected


def test_student_can_signup_again_after_unregistering(client):
    original = client.get("/activities").json()
    expected = deepcopy(original)
    assert NEW_EMAIL not in expected[ACTIVITY_NAME]["participants"]
    expected[ACTIVITY_NAME]["participants"].append(NEW_EMAIL)

    for method in ["POST", "DELETE", "POST"]:
        response = client.request(method, SIGNUP_PATH, params={"email": NEW_EMAIL})

        assert response.status_code == 200
        action = "Unregistered" if method == "DELETE" else "Signed up"
        preposition = "from" if method == "DELETE" else "for"
        assert response.json() == {
            "message": f"{action} {NEW_EMAIL} {preposition} {ACTIVITY_NAME}"
        }
        assert client.get("/activities").json() == (
            original if method == "DELETE" else expected
        )