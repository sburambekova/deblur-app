"""Errors raised by services. main.py turns them into HTTP responses, so services know nothing
about HTTP."""


class NotFoundError(Exception):
    """No such photo, job or gallery item (404)."""


class InvalidInputError(Exception):
    """The uploaded file is not a usable image (400)."""


class ConflictError(Exception):
    """The request does not fit the current state, e.g. the job is not done yet (409)."""
