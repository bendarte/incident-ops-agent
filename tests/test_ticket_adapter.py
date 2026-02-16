from pathlib import Path

from ticket_adapter import MockTicketAdapter


def test_mock_ticket_adapter_reset_store(tmp_path):
    storage = Path(tmp_path) / "tickets_adapter.json"
    adapter = MockTicketAdapter(storage_path=storage)

    created = adapter.create_ticket(
        title="Web down",
        description="503 on all endpoints",
        severity="Critical",
        confirm=True,
    )
    assert "INC-1" in created

    adapter.reset_store()
    not_found = adapter.get_ticket_status("INC-1")
    assert "not found" in not_found.lower()

    created_again = adapter.create_ticket(
        title="DB latency",
        description="P95 increased",
        severity="High",
        confirm=True,
    )
    assert "INC-1" in created_again
