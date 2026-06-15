from app.application.dto.transfer import ConfirmTransferRequest, CreateTransferRequest, TransferResponse
from app.domain.exceptions import (
    FestivalierInconnuException,
    TransferInsufficientTokensException,
    TransferLimitExceededException,
    TransferNotFoundException,
    TransferNotPendingException,
    TransferUnauthorizedException,
)
from app.domain.use_cases.confirm_transfer import ConfirmTransferCommand, ConfirmTransferUseCase
from app.domain.use_cases.create_transfer import CreateTransferCommand, CreateTransferUseCase
from app.domain.use_cases.get_transfer import GetTransferCommand, GetTransferUseCase


class TransferController:
    """Controller handling token transfer endpoints.

    HTTP status mapping:
    - 201  — transfer request created
    - 200  — transfer retrieved or finalized
    - 400  — malformed request (missing/invalid fields)
    - 403  — confirming user is not the recipient
    - 404  — transfer or festivalier not found
    - 409  — business rule violation (limit exceeded or insufficient tokens)
    - 422  — transfer is not in a state that allows the operation
    """

    def __init__(
        self,
        create_transfer_use_case: CreateTransferUseCase,
        get_transfer_use_case: GetTransferUseCase,
        confirm_transfer_use_case: ConfirmTransferUseCase,
    ) -> None:
        self.create_transfer_use_case = create_transfer_use_case
        self.get_transfer_use_case = get_transfer_use_case
        self.confirm_transfer_use_case = confirm_transfer_use_case

    # ── POST /transfers ───────────────────────────────────────────────────────

    def create_transfer(self, req: CreateTransferRequest) -> TransferResponse:
        """Create a pending token transfer request and reserve the sender's tokens."""
        errors = self._validate_create_request(req)
        if errors:
            return TransferResponse(400, {"errors": errors})

        try:
            transfer = self.create_transfer_use_case.execute(
                CreateTransferCommand(
                    sender_id=req.from_id,
                    recipient_id=req.to_id,
                    drink_tokens=req.drink_tokens,
                    food_tokens=req.food_tokens,
                )
            )
        except TransferLimitExceededException as exc:
            return TransferResponse(409, {"error": str(exc)})
        except FestivalierInconnuException as exc:
            return TransferResponse(404, {"error": str(exc)})
        except TransferInsufficientTokensException as exc:
            return TransferResponse(409, {"error": str(exc)})

        return TransferResponse(
            201,
            {
                "transferId": transfer.id,
                "status": transfer.status,
                "senderId": transfer.sender_id,
                "recipientId": transfer.recipient_id,
                "drinkTokens": transfer.drink_tokens,
                "foodTokens": transfer.food_tokens,
            },
        )

    # ── GET /transfers/{id} ───────────────────────────────────────────────────

    def get_transfer(self, transfer_id: str) -> TransferResponse:
        """Return the current status of a token transfer."""
        try:
            transfer = self.get_transfer_use_case.execute(GetTransferCommand(transfer_id=transfer_id))
        except TransferNotFoundException as exc:
            return TransferResponse(404, {"error": str(exc)})

        return TransferResponse(
            200,
            {
                "transferId": transfer.id,
                "status": transfer.status,
                "senderId": transfer.sender_id,
                "recipientId": transfer.recipient_id,
                "drinkTokens": transfer.drink_tokens,
                "foodTokens": transfer.food_tokens,
            },
        )

    # ── POST /transfers/{id}/confirm ──────────────────────────────────────────

    def confirm_transfer(self, req: ConfirmTransferRequest) -> TransferResponse:
        """Recipient accepts or rejects a pending token transfer."""
        if req.accept is None:
            return TransferResponse(400, {"errors": [{"field": "accept", "message": "accept is required"}]})

        try:
            transfer = self.confirm_transfer_use_case.execute(
                ConfirmTransferCommand(
                    transfer_id=req.transfer_id,
                    confirming_user_id=req.confirming_user_id,
                    accept=req.accept,
                    rejection_reason=req.rejection_reason,
                )
            )
        except TransferNotFoundException as exc:
            return TransferResponse(404, {"error": str(exc)})
        except TransferNotPendingException as exc:
            return TransferResponse(422, {"error": str(exc)})
        except TransferUnauthorizedException as exc:
            return TransferResponse(403, {"error": str(exc)})
        except FestivalierInconnuException as exc:
            return TransferResponse(404, {"error": str(exc)})

        return TransferResponse(
            200,
            {
                "transferId": transfer.id,
                "status": transfer.status,
                "resolvedAt": transfer.resolved_at,
            },
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _validate_create_request(self, req: CreateTransferRequest) -> list:
        errors = []
        if not req.from_id:
            errors.append({"field": "from_id", "message": "from_id is required"})
        if not req.to_id:
            errors.append({"field": "to_id", "message": "to_id is required"})
        if req.drink_tokens is None or not isinstance(req.drink_tokens, int) or req.drink_tokens < 0:
            errors.append({"field": "drink_tokens", "message": "drink_tokens must be a non-negative integer"})
        if req.food_tokens is None or not isinstance(req.food_tokens, int) or req.food_tokens < 0:
            errors.append({"field": "food_tokens", "message": "food_tokens must be a non-negative integer"})
        if not errors and req.drink_tokens == 0 and req.food_tokens == 0:
            errors.append({"field": "tokens", "message": "at least one token type must be greater than zero"})
        return errors
