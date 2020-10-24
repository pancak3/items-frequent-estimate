def sci(num: int):
    a = num
    b = 0

    while a > 9:
        a //= 10
        b += 1
    c = 10 ** b
    return r"${:.1f}\times10^{}$".format(num / c, b)
