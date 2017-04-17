import math


def abs_ratio(a, b):
    if a > b:
        return a / b
    else:
        return b / a


def is_harmony(f1, f2):
    # force floats with 1.0
    rat = abs_ratio(f1 * 1.0, f2)
    if float_equals(rat, int(rat)):
        return True
    else:
        return False


def float_equals(a, b):
    return abs(a - b) < 0.00001


if __name__ == '__main__':
    test_values = [0.05, 0.1, 0.3, 0.9, 1.0, 1.1, 3.0, 10.0]

    for i in test_values:
        x = abs(math.log(i))
        y = math.log(abs_ratio(1.0, i))
        print('{}, {}, {}, {}'.format(i, abs_ratio(i), x, y))
        assert float_equals(x, y)

    print('harmonies')
    print(is_harmony(100, 50))
    print(is_harmony(100, 20))
    print(is_harmony(100, 30))
