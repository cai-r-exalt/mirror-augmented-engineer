from app.application.dto.acknowledge_order import AcknowledgeOrderRequest, AcknowledgeOrderResponse
from app.domain.exceptions import (
    ArticleInconnuException,
    FestivalierInconnuException,
    OrderAlreadyAcknowledgedException,
    OrderNotAcknowledgeableException,
    OrderNotFoundException,
    StockInsuffisantException,
)
from app.domain.use_cases.acknowledge_order import AcknowledgeOrderCommand, AcknowledgeOrderUseCase


class AcknowledgeOrderController:
    """Controller handling POST /orders/{order_id}/acknowledge.

    HTTP status mapping:
    - 200  — order successfully acknowledged
    - 404  — order not found
    - 409  — stock insufficient at acknowledge time or item not in catalog
    - 422  — order is not in a state that allows acknowledgement
    """

    def __init__(self, acknowledge_order_use_case: AcknowledgeOrderUseCase) -> None:
        self.acknowledge_order_use_case = acknowledge_order_use_case

    def acknowledge_order(self, req: AcknowledgeOrderRequest) -> AcknowledgeOrderResponse:
        """Bartender acknowledges a pending order and receives an ETA."""
        try:
            order = self.acknowledge_order_use_case.execute(
                AcknowledgeOrderCommand(order_id=req.order_id)
            )
        except OrderNotFoundException as exc:
            return AcknowledgeOrderResponse(404, {"error": str(exc)})
        except OrderAlreadyAcknowledgedException as exc:
            return AcknowledgeOrderResponse(422, {"error": str(exc)})
        except OrderNotAcknowledgeableException as exc:
            return AcknowledgeOrderResponse(422, {"error": str(exc)})
        except (ArticleInconnuException, StockInsuffisantException) as exc:
            return AcknowledgeOrderResponse(422, {"error": str(exc)})
        except FestivalierInconnuException as exc:
            return AcknowledgeOrderResponse(404, {"error": str(exc)})

        return AcknowledgeOrderResponse(
            200,
            {
                "orderId": order.id,
                "status": order.status,
                "etaMinutes": order.eta_minutes,
                "acknowledgedAt": order.acknowledged_at,
            },
        )
