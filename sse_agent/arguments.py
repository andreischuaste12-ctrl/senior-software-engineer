"""Validators shared by the CLIs without depending on the entry-point module."""

import argparse
import math


def positive(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('Use a positive integer.')
    return number


def positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('Use a positive finite number.')
    return number
