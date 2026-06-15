from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TokenTransfer:
    """Records a token transfer request between two festival goers.

    Lifecycle:
    - PENDING: created and tokens reserved from sender's balance.
    - CONFIRMED: recipient accepted; tokens moved to recipient's balance.
    - REJECTED: recipient denied; sender's reservation released.
    """

    id: str
    sender_id: str
    recipient_id: str
    drink_tokens: int
    food_tokens: int
    status: str = field(default="PENDING")
    created_at: Optional[str] = field(default=None)
    resolved_at: Optional[str] = field(default=None)
