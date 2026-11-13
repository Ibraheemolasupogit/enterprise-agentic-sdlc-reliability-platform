"""C5-M02 TLS verification controls. Synthetic; never executed."""
import ssl
import urllib.request

import requests


def unsafe_requests(url):
    # ruleid: morrow.py.tls-verification-disabled
    return requests.get(url, timeout=5, verify=False)


def unsafe_context(url):
    # ruleid: morrow.py.tls-verification-disabled
    context = ssl._create_unverified_context()
    return urllib.request.urlopen(url, context=context, timeout=5)


def unsafe_hostname():
    context = ssl.create_default_context()
    # ruleid: morrow.py.tls-verification-disabled
    context.check_hostname = False
    # ruleid: morrow.py.tls-verification-disabled
    context.verify_mode = ssl.CERT_NONE
    return context


def safe_context(url, ca_file):
    # ok: morrow.py.tls-verification-disabled
    context = ssl.create_default_context(cafile=ca_file)
    return urllib.request.urlopen(url, context=context, timeout=5)


def safe_requests(url):
    # ok: morrow.py.tls-verification-disabled
    return requests.get(url, timeout=5, verify=True)
