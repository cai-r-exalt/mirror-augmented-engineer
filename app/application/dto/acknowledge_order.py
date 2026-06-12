from typing import Any, Dict


class AcknowledgeOrderRequest:
    """DTO for POST /orders/{order_id}/acknowledge."""

    def __init__(self, order_id: str) -> None:
        self.order_id = order_id


class AcknowledgeOrderResponse:
    def __init__(self, status_code: int, body: Dict[str, Any]) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> Dict[str, Any]:
        return self._body
