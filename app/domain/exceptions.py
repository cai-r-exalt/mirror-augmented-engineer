class StockInsuffisantException(Exception):
    def __init__(self, item_name: str):
        self.item_name = item_name
        super().__init__(f"Insufficient stock for {item_name}")


class ArticleInconnuException(Exception):
    def __init__(self, item_name: str):
        self.item_name = item_name
        super().__init__(f"Unknown article: {item_name}")


class ContributorBalanceExceededException(Exception):
    """Raised when a contributor's offered tokens exceed their available balance."""

    def __init__(self, festivalier_id: str, token_type: str):
        self.festivalier_id = festivalier_id
        self.token_type = token_type
        super().__init__(
            f"Contributor {festivalier_id} offered more {token_type} tokens than their available balance"
        )


class InsufficientPooledFundsException(Exception):
    """Raised when the pooled contributions cannot cover the total order cost."""

    def __init__(self, token_type: str, required: int, pooled: int):
        self.token_type = token_type
        self.required = required
        self.pooled = pooled
        super().__init__(
            f"Insufficient pooled {token_type} tokens: required {required}, pooled {pooled}"
        )


class FestivalierInconnuException(Exception):
    """Raised when a contributor's festivalier_id is not found."""

    def __init__(self, festivalier_id: str):
        self.festivalier_id = festivalier_id
        super().__init__(f"Unknown festivalier: {festivalier_id}")
