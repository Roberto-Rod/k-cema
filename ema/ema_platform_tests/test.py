#!/usr/bin/env python3


class Test:
    @staticmethod
    def lim(value, minimum, maximum):
        return (value >= minimum) and (value <= maximum)

    @staticmethod
    def nom(value, nominal, allowed_error_percent):
        allowed_error = abs(nominal) * (allowed_error_percent / 100)
        return Test.lim(value, nominal - allowed_error, nominal + allowed_error)


if __name__ == "__main__":
    print("This module is not intended to be executed stand-alone")
