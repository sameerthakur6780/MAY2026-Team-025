from flask import request

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def paginate_query(query, serialize):
    """Paginates a SQLAlchemy query using ?page=&per_page= query params and
    serializes each item with the given function."""
    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    page = max(page, 1)

    try:
        per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
    except (TypeError, ValueError):
        per_page = DEFAULT_PER_PAGE
    per_page = max(1, min(per_page, MAX_PER_PAGE))

    result = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        "items": [serialize(item) for item in result.items],
        "page": result.page,
        "per_page": result.per_page,
        "total": result.total,
        "pages": result.pages,
    }
