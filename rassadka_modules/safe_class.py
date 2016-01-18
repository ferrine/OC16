import pandas as pd


class SafeClass:
    @staticmethod
    def _check_settings(fact, req, way=">="):
        """
        Проверка на то, что все необходимые настройки были во входных данных
        :param fact: set
        :param req: set
        :return: None or Exception
        """
        if way not in {">=", "<=", "==", ">", "<"}:
            raise TypeError
        command = "{fact} {way} {req}".format(fact=fact, way=way, req=req)
        result = eval(command)
        return result

    @staticmethod
    def _check_values_condition(fact, req):
        """
        Условия находятся в словаре. Словарь устроен так:
        по ключу названия проверяемой переменной достается нужная функция
            *я в своей реализации буду использовать объект функции, чтобы был норм вывод
        Вот пример
        req = lambda x: x>0         # необходимое условие - больше нуля
        fact = 1                    # fact удовлетворяет условию
        res = req(1)                # вернет True
        :param fact: dictionary
        :param req: dictionary
        :return: True
        """
        result = True
        for f in fact:
            if req.get(f) is not None:
                res = req[f](fact[f])
                result = result and res
        return result

    @staticmethod
    def _check_nans(fact):
        """
        На вход идет матрица или таблица полностью,
        далее будет проверено нет ли там отсутствующих
        значений или ошибки размерности
        :param fact: matrix or DataFrame
        :return: None or Exception
        """
        result = not any(pd.isnull(item) for item in fact.flatten())
        return result

    @staticmethod
    def _check_shape(fact, req):
        result = True
        if req:
            result = fact == req
        return result
