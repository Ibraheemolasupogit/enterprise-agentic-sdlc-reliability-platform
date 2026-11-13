"""C5-M08 inline suppression must not hide a mandatory control (--disable-nosem)."""


def suppressed(expression):
    # ruleid: morrow.py.unsafe-eval-or-deserialization
    return eval(expression)  # nosemgrep
