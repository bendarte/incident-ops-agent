from pathlib import Path

import tools
from ticket_adapter import MockTicketAdapter


def test_ticket_lifecycle_requires_confirmation_and_persists(tmp_path):
    original_adapter = tools._ticket_adapter
    tools._ticket_adapter = MockTicketAdapter(storage_path=Path(tmp_path) / "tickets_test.json")
    try:
        not_confirmed = tools.create_ticket.invoke(
            {"title": "DB latency", "description": "Slow queries", "severity": "High", "confirm": False}
        )
        assert "Confirmation required" in not_confirmed

        created = tools.create_ticket.invoke(
            {"title": "DB latency", "description": "Slow queries", "severity": "High", "confirm": True}
        )
        assert "INC-1" in created

        status = tools.get_ticket_status.invoke({"ticket_id": "INC-1"})
        assert "Status: Open" in status

        updated = tools.update_ticket_status.invoke({"ticket_id": "INC-1", "new_status": "Resolved", "confirm": True})
        assert "status updated" in updated

        status_after = tools.get_ticket_status.invoke({"ticket_id": "INC-1"})
        assert "Status: Resolved" in status_after
    finally:
        tools._ticket_adapter = original_adapter
