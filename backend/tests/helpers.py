def first_track(client, headers):
    tracks = client.get("/tracks", headers=headers)
    assert tracks.status_code == 200
    return tracks.json()[0]


def first_lesson_id(client, headers):
    track = client.get(f"/tracks/{first_track(client, headers)['id']}", headers=headers)
    assert track.status_code == 200
    return track.json()["recommended_lesson"]["id"]


def first_multiple_choice_question(client, headers, lesson_id: int):
    lesson = client.get(f"/lessons/{lesson_id}", headers=headers)
    assert lesson.status_code == 200
    return next(
        item
        for item in lesson.json()["questions"]
        if item["question_type"] == "multiple_choice"
    )


def correct_option_label(question: dict) -> str:
    # Seeded multiple-choice questions use B/A/A as correct labels; the public
    # API intentionally hides correctness, so tests use the known seed answer.
    if "return" in question["prompt"].lower() or "function design" in question["prompt"].lower():
        return "B"
    return "A"
