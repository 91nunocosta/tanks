from dataclasses import dataclass

import pytest


@dataclass
class BaseTestCase:
    name: str


def parametrize(*cases: BaseTestCase):
    def wrapper(test_function):
        return pytest.mark.parametrize(
            argnames="case", argvalues=list(cases), ids=lambda case: case.name
        )(test_function)

    return wrapper
