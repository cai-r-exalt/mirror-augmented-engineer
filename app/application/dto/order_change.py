from typing import Any, Dict, List, Optional


class ModifyOrderRequest:
    """DTO for PATCH /orders/{order_id} — direct modification of an unacknowledged order."""

    def __init__(self, order_id: str, items: Optional[List[Dict[str, Any]]]) -> None:
        self.order_id = order_id
        self.items = items


class CreateChangeRequestRequest:
    """DTO for POST /orders/{order_id}/change-requests."""

    def __init__(self, order_id: str, proposed_items: Optional[List[Dict[str, Any]]]) -> None:
        self.order_id = order_id
        self.proposed_items = proposed_items


class ResolveChangeRequestRequest:
    """DTO for POST /orders/{order_id}/change-requests/{req_id}/resolve."""

    def __init__(
        self,
        order_id: str,
        request_id: str,
        accept: bool,
        rejection_reason: Optional[str] = None,
        resolver_id: Optional[str] = None,
    ) -> None:
        self.order_id = order_id
        self.request_id = request_id
        self.accept = accept
        self.rejection_reason = rejection_reason
        self.resolver_id = resolver_id


class OrderChangeResponse:
    def __init__(self, status_code: int, body: Dict[str, Any]) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> Dict[str, Any]:
        return self._body
