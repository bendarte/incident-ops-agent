from pathlib import Path

import tools


def test_ticket_lifecycle_requires_confirmation_and_persists(tmp_path):
    original_path = tools._TICKETS_PATH
    tools._TICKETS_PATH = Path(tmp_path) / "tickets_test.json"
    try:
        api = tools.MockTicketAPI()

        not_confirmed = api.create_ticket.func(
            api, "DB latency", "Slow queries", "High", False
        )
        assert "Confirmation required" in not_confirmed

        created = api.create_ticket.func(
            api, "DB latency", "Slow queries", "High", True
        )
        assert "INC-1" in created

        status = api.get_ticket_status.func(api, "INC-1")
        assert "Status: Open" in status

        updated = api.update_ticket_status.func(api, "INC-1", "Resolved", True)
        assert "status updated" in updated

        status_after = api.get_ticket_status.func(api, "INC-1")
        assert "Status: Resolved" in status_after
    finally:
        tools._TICKETS_PATH = original_path
