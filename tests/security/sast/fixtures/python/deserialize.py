"""C5-M05 eval/deserialization controls. Synthetic; never executed."""
import json
import pickle

import yaml


def unsafe_eval(expression):
    # ruleid: morrow.py.unsafe-eval-or-deserialization
    return eval(expression)


def unsafe_pickle(data):
    # ruleid: morrow.py.unsafe-eval-or-deserialization
    return pickle.loads(data)


def unsafe_yaml(text):
    # ruleid: morrow.py.unsafe-eval-or-deserialization
    return yaml.load(text, Loader=yaml.Loader)


def safe_yaml(text):
    # ok: morrow.py.unsafe-eval-or-deserialization
    return yaml.load(text, Loader=yaml.BaseLoader)


def safe_json(text):
    # ok: morrow.py.unsafe-eval-or-deserialization
    return json.loads(text)
