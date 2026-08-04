class PaginatedResponse[T](GenericModel):  # noqa: F821
    items: list[T]
    total: int
    skip: int
    limit: int
    has_next: bool