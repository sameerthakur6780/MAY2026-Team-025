class ApiError(Exception):
    def __init__(self, message, code="error", status_code=400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def not_found(resource):
    return ApiError(f"{resource} not found", "not_found", 404)


def forbidden(message="You do not have access to this resource"):
    return ApiError(message, "forbidden", 403)
