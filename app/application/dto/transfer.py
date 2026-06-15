from typing import Any, Dict, Optional


class CreateTransferRequest:
    """DTO for POST /transfers."""

    def __init__(self, from_id: str, to_id: str, drink_tokens: int, food_tokens: int) -> None:
        self.from_id = from_id
        self.to_id = to_id
        self.drink_tokens = drink_tokens
        self.food_tokens = food_tokens


class ConfirmTransferRequest:
    """DTO for POST /transfers/{id}/confirm."""

    def __init__(
        self,
        transfer_id: str,
        confirming_user_id: str,
        accept: bool,
        rejection_reason: Optional[str] = None,
    ) -> None:
        self.transfer_id = transfer_id
        self.confirming_user_id = confirming_user_id
        self.accept = accept
        self.rejection_reason = rejection_reason


class TransferResponse:
    """Generic response wrapper for transfer endpoints."""

    def __init__(self, status_code: int, body: Dict[str, Any]) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> Dict[str, Any]:
        return self._body
