class PaginatedResponse[T](GenericModel):
    items: list[T]
    total: int
    skip: int
    limit: int
    has_next: bool