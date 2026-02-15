from __future__ import annotations

from typing import Union, NamedTuple

def percentage_from_whole_and_part(part: Union[int, float], whole: Union[int, float]):
    return ((part / whole) * 100)

def part_from_whole_and_percentage(percentage: Union[int, float], whole: Union[int, float]):
    return (percentage * whole)

def whole_from_part_and_percentage(part: Union[int, float], percentage: Union[int, float]):
    return (part / percentage)

def if_whole_is_none(whole, part, percentage):
    if whole is None and part is not None and percentage is not None:
        return (whole_from_part_and_percentage(part, percentage), part, percentage)
    return (whole, part, percentage)

def if_part_is_none(whole, part, percentage):
    if part is None and whole is not None and percentage is not None:
        return (whole, part_from_whole_and_percentage(percentage, whole), percentage)
    return (whole, part, percentage)

def if_percentage_is_none(whole, part, percentage):
    if percentage is None and part is not None and whole is not None:
        return (whole, part, percentage_from_whole_and_part(whole, part))
    return (whole, part, percentage)

def ensure_percentage_params(whole, part, percentage):
    return if_whole_is_none(if_part_is_none(if_percentage_is_none(whole, part, percentage)))

def percentage_params(*args, **kwargs):
    whole = kwargs.get('whole', None)
    part = kwargs.get('part', None)
    percentage = kwargs.get('percentage', None)
    if whole is None and len(args) >= 1:
        whole = args[0]
    if part is None and len(args) >= 2:
        part = args[1]
    if percentage is None and len(args) >= 3:
        percentage = args[2]

    empty_params = [whole, part, percentage].count(None)
    if not empty_params:
        return ("_validation_", whole, part, percentage)
    elif empty_params == 1:
        return ("_calculation_", whole, part, percentage)
    else:
        return ("_insufficient_values_", whole, part, percentage)

def compare_calculation_part_percentage(whole, part, percentage):
    return (whole == whole_from_part_and_percentage(part, percentage))

def compare_calculation_percentage_whole(whole, part, percentage):
    return (part == part_from_whole_and_percentage(whole, percentage))

def compare_calculation_whole_part(whole, part, percentage):
    return (percentage == percentage_from_whole_and_part(whole, part))

def calculation_comparison(whole, part, percentage):
    return (
        compare_calculation_part_percentage(whole, part, percentage),
        compare_calculation_percentage_whole(whole, part, percentage),
        compare_calculation_whole_part(whole, part, percentage),
        )

class Percentage(NamedTuple):
    whole: Union[int, float]
    part: Union[int, float]
    percentage: Union[int, float]

def percent(*args, **kwargs):
    call_type, whole, part, percentage = percentage_params(*args, **kwargs)
    if call_type == "_validation_":
        return bool(all(calculation_comparison(whole, part, percentage)))
    if call_type == "_calculation_":
        return Percentage(ensure_percentage_params(whole, part, percentage))
    if call_type == "_insufficient_values_":
        raise ValueError(str(args), str(kwargs))
