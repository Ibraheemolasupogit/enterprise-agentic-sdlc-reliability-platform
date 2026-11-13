"""C5-M04 process execution controls. Synthetic; never executed."""
import os
import subprocess


def unsafe_shell(branch):
    # ruleid: morrow.py.process-shell
    subprocess.run(f"git log {branch}", shell=True, check=True)


def unsafe_system(path):
    # ruleid: morrow.py.process-shell
    os.system("ls " + path)


def safe_argv(branch):
    # ok: morrow.py.process-shell
    subprocess.run(["git", "log", "--", branch], check=True, timeout=60)


def missed_alias(command):
    run = subprocess.run
    flag = True
    # todoruleid: morrow.py.process-shell
    run(command, shell=flag)
