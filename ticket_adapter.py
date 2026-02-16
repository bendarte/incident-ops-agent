from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


VALID_TICKET_STATUSES = ["Open", "In Progress", "Resolved", "Closed", "On Hold"]


class TicketAdapter(ABC):
    @abstractmethod
    def create_ticket(self, title: str, description: str, severity: str, confirm: bool) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_ticket_status(self, ticket_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def update_ticket_status(self, ticket_id: str, new_status: str, confirm: bool) -> str:
        raise NotImplementedError

    @abstractmethod
    def reset_store(self) -> None:
        raise NotImplementedError


class MockTicketAdapter(TicketAdapter):
    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self.tickets: dict[str, dict[str, Any]] = {}
        self.ticket_id_counter = 1
        self._load()

    def _load(self) -> None:
        if self._storage_path.exists():
            try:
                data = json.loads(self._storage_path.read_text(encoding="utf-8"))
                self.tickets = data.get("tickets", {})
                self.ticket_id_counter = int(data.get("ticket_id_counter", 1))
            except Exception:
                self.tickets = {}
                self.ticket_id_counter = 1

    def _save(self) -> None:
        payload = {
            "ticket_id_counter": self.ticket_id_counter,
            "tickets": self.tickets,
        }
        self._storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def create_ticket(self, title: str, description: str, severity: str, confirm: bool) -> str:
        if not confirm:
            return (
                "Confirmation required. Re-run create_ticket with confirm=True after you verify:\n"
                f"- title='{title}'\n- severity='{severity}'\n"
                "This prevents accidental ticket creation."
            )

        new_ticket_id = f"INC-{self.ticket_id_counter}"
        self.tickets[new_ticket_id] = {
            "title": title,
            "description": description,
            "severity": severity,
            "status": "Open",
        }
        self.ticket_id_counter += 1
        self._save()
        return f"Ticket '{new_ticket_id}' created successfully with title: '{title}' and severity: '{severity}'."

    def get_ticket_status(self, ticket_id: str) -> str:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return f"Error: Ticket '{ticket_id}' not found."
        return (
            f"Ticket ID: {ticket_id}\n"
            f"Title: {ticket['title']}\n"
            f"Description: {ticket['description']}\n"
            f"Severity: {ticket['severity']}\n"
            f"Status: {ticket['status']}"
        )

    def update_ticket_status(self, ticket_id: str, new_status: str, confirm: bool) -> str:
        if new_status not in VALID_TICKET_STATUSES:
            return f"Error: Invalid status '{new_status}'. Valid statuses are: {', '.join(VALID_TICKET_STATUSES)}."

        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return f"Error: Ticket '{ticket_id}' not found."

        if not confirm:
            return (
                "Confirmation required. Re-run update_ticket_status with confirm=True after you verify:\n"
                f"- ticket_id='{ticket_id}'\n- new_status='{new_status}'"
            )

        ticket["status"] = new_status
        self._save()
        return f"Ticket '{ticket_id}' status updated to '{new_status}'."

    def reset_store(self) -> None:
        self.tickets = {}
        self.ticket_id_counter = 1
        self._save()
