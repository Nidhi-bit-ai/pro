from datetime import datetime, timezone


def _base_event(event_type: str):

    return {
        "type": event_type,
        "timestamp": datetime.now(
            timezone.utc,
        ).isoformat(),
    }


def status_event(
    stage: str,
    message: str,
):

    event = _base_event("status")

    event.update(
        {
            "stage": stage,
            "message": message,
        }
    )

    return event


def final_event(data):

    event = _base_event("final")

    event["data"] = data

    return event


def error_event(message: str):

    event = _base_event("error")

    event["message"] = message

    return event