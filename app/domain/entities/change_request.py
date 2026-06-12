from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChangeRequest:
    """Records a proposed modification to an already-acknowledged order.

    A bartender must resolve (accept or reject) the request. When accepted,
    the underlying order's items are updated. When rejected, the rejection
    reason is recorded and the festivalier is notified.
    """

    id: str
    order_id: str
    proposed_items: List[Dict[str, Any]]
    status: str = field(default="EN_ATTENTE_REVIEW")
    rejection_reason: Optional[str] = field(default=None)
