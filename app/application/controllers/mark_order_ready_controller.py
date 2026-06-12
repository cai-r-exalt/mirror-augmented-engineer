from app.application.dto.mark_order_ready import MarkOrderReadyRequest, MarkOrderReadyResponse
from app.domain.exceptions import (
    OrderNotFoundException,
    OrderNotReadyTransitionableException,
    PreparedStockInsuffisantException,
)
from app.domain.use_cases.mark_order_ready import (
    DEFAULT_PICKUP_DETAILS,
    MarkOrderReadyCommand,
    MarkOrderReadyUseCase,
)


class MarkOrderReadyController:
    """Controller handling POST /orders/{order_id}/ready."""

    def __init__(self, mark_order_ready_use_case: MarkOrderReadyUseCase) -> None:
        self.mark_order_ready_use_case = mark_order_ready_use_case

    def mark_order_ready(self, req: MarkOrderReadyRequest) -> MarkOrderReadyResponse:
        try:
            order = self.mark_order_ready_use_case.execute(
                MarkOrderReadyCommand(
                    order_id=req.order_id,
                    pickup_details=req.pickup_details or DEFAULT_PICKUP_DETAILS,
                )
            )
        except OrderNotFoundException as exc:
            return MarkOrderReadyResponse(404, {"error": str(exc)})
        except PreparedStockInsuffisantException as exc:
            return MarkOrderReadyResponse(409, {"error": str(exc)})
        except OrderNotReadyTransitionableException as exc:
            return MarkOrderReadyResponse(422, {"error": str(exc)})

        return MarkOrderReadyResponse(
            200,
            {
                "orderId": order.id,
                "status": order.status,
                "readyAt": order.ready_at,
            },
        )
