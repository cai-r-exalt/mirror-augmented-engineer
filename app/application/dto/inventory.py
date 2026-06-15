from typing import Any, Dict, Optional


class UpdateStockRequest:
    """DTO for PATCH /inventory/{item_id}."""

    def __init__(self, item_id: str, quantity: Optional[int]) -> None:
        self.item_id = item_id
        self.quantity = quantity


class UpdateStockResponse:
    def __init__(self, status_code: int, body: Dict[str, Any]) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> Dict[str, Any]:
        return self._body
