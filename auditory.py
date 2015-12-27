import pandas as pd
from excelprocessor.reader import splitter
import datetime
import numpy as np
import sys


class AuditoryException(Exception):
    lg = "debug.txt"

    def __init__(self, current=None, expected=None, name=None):
        self.current = current
        self.expected = expected
        self.situation_name = name

    def header(self):
        line = "="*10 + " "*5 + "{0: <25}".format(type(self).__name__) + "="*5 +\
               "\n" + datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p") + "\n\n" +\
               "In " + self.situation_name + "\n"
        return line

    @staticmethod
    def ender():
        line = "~"*5 + "\n"*3
        return line

    def message(self):
        mes = "Called " + type(self).__name__
        return mes

    def logerror(self):
        with open(self.lg, "a") as log:
            log.write(self.header())
            log.write(self.message())
            log.write(self.ender())

    def __str__(self):
        self.logerror(self)
        return "\n" + self.message() + "See more info in " + self.lg


class NotEnoughSettings(AuditoryException):
    def message(self):
        mes = """
        Settings expected:\t{exp}
        Settings got:\t\t{cur}
        Please fix\t\t{ce}
        Please add\t\t{ec}
""".format(exp=self.expected,
           cur=self.current,
           ce=self.current - self.expected,
           ec=self.expected - self.current)
        return mes


class WrongNumberOfInstances(AuditoryException):
    def message(self):
        mes = """
        Required frequency:\t{exp}
        Input frequency:\t\t{cur}
""".format(exp=self.expected,
           cur=self.current)
        return mes


class WrongMatrixInput(AuditoryException):
    problem = "Something is wrong, I don't know exactly what"

    def solution(self):
        return "Check all requirements, please"

    def message(self):
        mes = """
        There is a problem with Matrix Input

        Description:
        {problem}

        Solution:
        {solution}
""".format(problem=self.problem,
                   solution=self.solution())
        return mes


class NansInMatrix(WrongMatrixInput):
    problem = "Missing Values"

    def solution(self):
        return "Fill in all empty cells in the table"


class WrongShape(WrongMatrixInput):
    problem = "Wrong Shape"

    def solution(self):
        solv = """
        \tChange shape of Matrix
        \tExpected Shape:\t{exp}
        \tInput Shape:\t{cur}
""".format(exp=self.expected,
           cur=self.current)
        return solv



class Auditory:
    """
    это основной способ реализации аудиторий для рассадки
    этот класс должен поддерживать следующие методы:

    1) Инициализация из таблицы Pandas/матрицы Numpy, которая поидее должна
    будет импортироваться из внешнего файла при работе алгоритма, далее все
    аудитории будут помещены в список и обрабатываться алгоритмом
        * при инициализации надо будет продумать как присваивать настрайки
        для конкретной аудитории
        * скорее всего потребуется наследование класса для обработки
        поточных аудиторий, поэтому надо предусмотреть это расширение
    2) проверка на возможность посадки в соответствии с правилами рассадки
    общие правила будут передаваться в качестве аргумента, частные для
    аудитории будут храниться в самом классе
    3) вставка участников
    4) изъятие участников
    5) поддержка проверки вместимости аудитории, вывод числа свободных мест
    6) ячейки матрицы мест должны быть составными
    Имеется ввиду поддержка двойной нумерации, абсолютной для метода проверки
    и относительной для вывода на печать рассадки
    """
    _required_general_options = {"settings", "seats", "klass", "school"}

    _required_settings_options = {"name", "available", "class_8", "class_9",
                             "class_10", "class_11", "individual", "command"}

    _required_klass_values = {'Далеко', 'Рядом', 'Участник'}

    _required_school_values = {'Далеко', 'Рядом', 'Участник'}

    _required_seats_values = {'Место', 'Проход'}

    _standard_settings_column_names = ["key", "description", "code", "result"]

    _required_klass_values_condition = {"Далеко": None, "Рядом": None, "Участник": " == 1"}

    _required_school_values_condition = {"Далеко": None, "Рядом": None, "Участник": " == 1"}

    _required_settings_values_condition = {"name": None,
                                           "available": " in {0, 1}",
                                           "class_8": " in {0, 1}",
                                           "class_9": " in {0, 1}",
                                           "class_10": " in {0, 1}",
                                           "class_11": " in {0, 1}",
                                           "individual": " in {0, 1}",
                                           "command": " in {0, 1}"}

    _required_klass_shape = (7, 7)

    _required_school_shape = (7, 7)

    _required_seats_shape = None

    _required_settings_shape = (9, 4)

    def _debug_message(self, test_name, result):
        end = {True: "Success", False: "Fail"}[result]
        print("{0: >35} for {1: >10} : {2}".format(test_name, self.outer_name, end))

    def _silent_check_settings(self, fact, req, name=None):
        """
        Проверка на то, что все необходимые настройки были во входных данных
        :param fact: set
        :param req: set
        :param name: string
        :return: None or Exception
        """
        result = req == fact
        if __debug__:
            self._debug_message(name, result)
        if req == fact:     # Проверка, что необходимые аргументы есть подмножество указанных
            pass
        else:               # Иначе возбуждаем исключение
            raise NotEnoughSettings(current=fact, expected=req, name=name + " of " + self.outer_name)

    def _silent_check_values_condition(self, fact, req, name=None):
        """
        Условия в req находятся в словаре в строковом виде
        проверяемое условие является левым операндом
        пример:
        req = " >= 0"               # необходимое условие - больше нуля
        fact = 1                    # fact удовлетворяет условию
        res = eval(str(fact) + req) # вернет True
        :param fact: dictionary
        :param req: dictionary
        :param name: string
        :return: None or Exception
        """
        result = True   # Проверяется условие для фактически указанных переменных
        for f in fact:  # Ожидается, что проверка на наличие всех необходимых уже пройдена
            if req[f] is not None:
                res = eval(str(fact[f]) + req[f])
                assert isinstance(res, bool), "Result of comparison is not bool (" + str(result) + ")"
                result = result and res
        if __debug__:
            self._debug_message(name, result)
        if result:
            pass
        else:
            raise WrongNumberOfInstances(current=fact, expected=req, name=name + " of " + self.outer_name)

    def _silent_check_shape(self, fact, req, name=None):
        """
        На вход идет матрица или таблица полностью,
        далее будет проверено нет ли там отсутствующих
        значений или ошибки размерности
        :param fact: matrix or DataFrame
        :param req: (x, y) shape or None if no restrictions
        :param name: dict
        :return: None or Exception
        """
        has_nan = any(pd.isnull(item) for item in fact.flatten())
        good_shape = True
        if req:
            good_shape = fact.shape == req
        result = good_shape and not has_nan
        if __debug__:
            self._debug_message(name, result)
        if good_shape:
            pass
        else:
            raise WrongShape(current=fact.shape, expected=req, name=name + " of " + self.outer_name)
        if has_nan:
            raise NansInMatrix(name=name + " of " + self.outer_name)

    def get_settings(self, raw):
        # Сначала проверяем целостность ввода
        self._silent_check_settings(fact=set(raw.keys()),
                                    req=self._required_general_options,
                                    name="General Auditory Options Check")
        # Проверяем наличие ошибок неправильного заполнения таблицы свойств
        self._silent_check_shape(fact=raw["settings"],
                                 req=self._required_settings_shape,
                                 name="Settings Shape Check")
        settings = pd.DataFrame(raw["settings"][1:], columns=raw["settings"][0])
        settings.columns = self._standard_settings_column_names
        settings.set_index("key", inplace=True)
        # Затем проверяем все ли настнойки внесены в табличку
        self._silent_check_settings(fact=set(settings.index),
                                    req=self._required_settings_options,
                                    name="Specific Auditory Options Check")
        self._silent_check_values_condition(fact=settings["code"].to_dict(),
                                            req=self._required_settings_values_condition,
                                            name="Settings Values Check")
        # Если с основной табличкой все впорядке, переходим к матрице близости для одного класса
        klass_condition = raw["klass"]
        self._silent_check_shape(fact=klass_condition,
                                 req=self._required_klass_shape,
                                 name="Klass Shape Check")
        key, frequency = np.unique(klass_condition.flatten(), return_counts=True)
        # Проверяем есть ли там ожидаемые значения
        self._silent_check_settings(fact=set(key),
                                    req=self._required_klass_values,
                                    name="Klass Values Check")
        klass_freq_dict = dict(zip(key, frequency))
        # Проверяем, что там указано ровно одно место для участника
        self._silent_check_values_condition(fact=klass_freq_dict,
                                            req=self._required_klass_values_condition,
                                            name="Klass Values Condition Check")
        # Делаем все то же самое для матрицы близости школы
        school_condition = raw["school"]
        self._silent_check_shape(fact=school_condition,
                                 req=self._required_school_shape,
                                 name="School Shape Check")
        key, frequency = np.unique(klass_condition.flatten(), return_counts=True)
        # Значения заполненных ячеек
        self._silent_check_settings(fact=set(key),
                                    req=self._required_klass_values,
                                    name="School Values Check")
        school_freq_dict = dict(zip(key, frequency))
        # Участник ровно один
        self._silent_check_values_condition(fact=school_freq_dict,
                                            req=self._required_klass_values_condition,
                                            name="School Values Condition Check")
        # Карта рассадки
        seats_map = raw["seats"]
        self._silent_check_shape(fact=seats_map,
                                 req=self._required_seats_shape,
                                 name="Seats Map Shape Check")
        key, frequency = np.unique(klass_condition.flatten(), return_counts=True)
        self._silent_check_settings(fact=set(key),
                                    req=self._required_klass_values,
                                    name="Seats Map Values Check")
        return dict([("settings", settings),
                     ("klass_condition", klass_condition),
                     ("school_condition", school_condition),
                     ("seats_map", seats_map)])

    def __init__(self, raw_settings, outer_name):
        self.outer_name = outer_name
        try:
            settings_dict = self.get_settings(raw_settings)
            self._settings_table = settings_dict["settings"]
            self._settings = settings_dict["settings"]["code"].to_dict()
            self._klass_condition_matrix = settings_dict["klass_condition"]
            self._school_condition_matrix = settings_dict["school_condition"]
            self._seats_map = settings_dict["seats_map"]
        except AuditoryException as e:
            e.logerror()

    def __str__(self):
        res = """
            settings:
{0}

            seats_shape: {1}

            klass_condition_matrix:
{2}

            school_condition_matrix:
{3}
""".format(self._settings, self._seats_map.shape,
           self._klass_condition_matrix,
           self._school_condition_matrix)
        return res
if __name__ == "__main__":
    pass