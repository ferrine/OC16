import unicodedata
from collections import OrderedDict as oDict


def mutable(method):
    """
    Чтобы избежать ругательств IDE и читателя, рекомендуется
    добавить метод update
    :param method:
    :return:
    """
    def wrapped(self, *args, **kwargs):
        method(self, *args, **kwargs)
        self.update()
    return wrapped


def clr(x):
    if isinstance(x, str):
        return unicodedata.normalize("NFD", x.strip())
    else:
        return x


class Ch:
        def __init__(self, func, description):
            self.func = func
            self.description = description

        def __str__(self):
            return str(self.description)

        def __call__(self, *args, **kwargs):
            if self.func is not None:
                return self.func(*args, **kwargs)
            else:
                return True


def swap(d):
    return oDict([(v, k) for k, v in d.items()])