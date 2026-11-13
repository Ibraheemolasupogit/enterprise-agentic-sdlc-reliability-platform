"""C5-M06 sensitive logging controls. Synthetic; never executed."""
import logging

logger = logging.getLogger(__name__)


def unsafe_print(access_token):
    # ruleid: morrow.py.sensitive-value-logged
    print("token", access_token)


def unsafe_logger(response):
    # ruleid: morrow.py.sensitive-value-logged
    logger.info("auth header %s", response.headers.authorization)


def safe_print(request_id, status):
    # ok: morrow.py.sensitive-value-logged
    print(f"request {request_id} finished with {status}")


def safe_literal():
    # ok: morrow.py.sensitive-value-logged
    print("Token validation failed; see the error code.")
