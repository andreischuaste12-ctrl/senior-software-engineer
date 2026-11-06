"""Validadores compartilhados pelos CLIs, sem dependência do módulo de entrada."""

import argparse
import math


def positive(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('Use um inteiro positivo.')
    return number


def positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('Use um número positivo finito.')
    return number
