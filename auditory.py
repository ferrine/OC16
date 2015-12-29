import numpy as np
import pandas as pd
from safe_class import SafeClass, Ch

from rassadka_exceptions import *


class Auditory(SafeClass):
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

    _required_klass_values_condition = {"Далеко": None, "Рядом": None, "Участник": Ch(lambda x: x == 1, "== 1")}

    _required_school_values_condition = {"Далеко": None, "Рядом": None, "Участник": Ch(lambda x: x == 1, "== 1")}

    _required_settings_values_condition = {"name": Ch(None, None),
                                           "available": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "class_8": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "class_9": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "class_10": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "class_11": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "individual": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "command": Ch(lambda x: x in {1, 0}, "in {0, 1}")}

    _required_klass_shape = (7, 7)

    _required_school_shape = (7, 7)

    _required_seats_shape = None

    _required_settings_shape = (9, 4)

    def _debug_message(self, test_name, result):
        end = {True: "Success", False: "Fail"}[result]
        print("{0: >35} for {1: >10} : {2}".format(test_name, self.outer_name, end))

    def get_clean_settings(self, raw):
        # Возможно покажется излишним код вызова исключений не интегрированный в сами проверки, но
        # в дальнейшем я предполагаю использование суперкласса где-нибудь еще и уж точно у меня
        # будет другой набор исключений, поэтому я решил сделать именно вот так.

        # Сначала проверяем целостность ввода
        if not self._check_settings(fact=set(raw.keys()),
                                    req=self._required_general_options):
            raise NotEnoughSettings(fact=set(raw.keys()),
                                    req=self._required_general_options,
                                    name="Проверка основных тегов на листе",
                                    aud=self.outer_name)
        # Проверяем наличие ошибок неправильного заполнения таблицы свойств
        if not self._check_shape(fact=raw["settings"].shape,
                                 req=self._required_settings_shape):
            raise WrongShapeException(fact=raw["settings"].shape,
                                      req=self._required_settings_shape,
                                      name="Проверка размерности таблицы с настройками аудитории",
                                      aud=self.outer_name)
        if not self._check_nans(fact=raw["settings"]):
            raise NansInMatrixException(name="Проверка наличия отсутствующих значений в настройках аудитории",
                                        aud=self.outer_name)
        # Чтобы проверить саму табличку надо проделать несколько махинаций, ведь по умолчанию все в виде матриц
        settings = pd.DataFrame(raw["settings"][1:], columns=raw["settings"][0])
        settings.columns = self._standard_settings_column_names
        settings.set_index("key", inplace=True)
        # Проверяем все ли настнойки внесены в табличку
        if not self._check_settings(fact=set(settings.index),
                                    req=self._required_settings_options):
            raise NotEnoughSettings(fact=set(settings.index),
                                    req=self._required_settings_options,
                                    name="Проверка вхождения всех необходимых\
переменных по ключу в настройках аудитории",
                                    aud=self.outer_name)
        # Проверяем, что это именно то, что мы ожидали получить на входе
        if not self._check_values_condition(fact=settings["code"].to_dict(),
                                            req=self._required_settings_values_condition):
            raise ValuesConditionException(fact=settings["code"].to_dict(),
                                           req=self._required_settings_values_condition,
                                           name="Проверка валидности ввода настроек в таблицу",
                                           aud=self.outer_name)

        # Если с основной табличкой все впорядке, переходим к матрице близости для одного класса
        # Тут махинаций делать не придется, нужна матрица
        klass_condition = raw["klass"]
        if not self._check_shape(fact=klass_condition.shape,
                                 req=self._required_klass_shape):
            raise WrongShapeException(fact=klass_condition.shape,
                                      req=self._required_klass_shape,
                                      name="Проверка размерности матрицы близости для класса",
                                      aud=self.outer_name)
        if not self._check_nans(fact=klass_condition):
            raise NansInMatrixException(name="Проверка наличия отсутствующих значений \
в матрице близости для класса",
                                        aud=self.outer_name)
        # Чтобы убелиться что там присутстуют все необходимые значения и их нужное количество,
        # Можно составить словарь(см ниже)
        key, frequency = np.unique(klass_condition.flatten(), return_counts=True)
        # Проверяем есть ли там ожидаемые значения
        if not self._check_settings(fact=set(key),
                                    req=self._required_klass_values,
                                    way="<="):
            raise NotEnoughSettings(fact=set(key),
                                    req=self._required_klass_values,
                                    name="Проверка на допустимые значения в матрице близости для класса\n\
Если там нет ни одного 'Близко', это будет считаться ошибкой",
                                    way="<=",
                                    aud=self.outer_name)
        klass_freq_dict = dict(zip(key, frequency))
        # Проверяем, что там указано ровно одно место для участника
        if not self._check_values_condition(fact=klass_freq_dict,
                                            req=self._required_klass_values_condition):
            raise ValuesConditionException(fact=klass_freq_dict,
                                           req=self._required_klass_values_condition,
                                           name="Проверка, что в матрице близости для класса ровно один 'Участник'",
                                           aud=self.outer_name)
        # Делаем все то же самое для матрицы близости школы
        school_condition = raw["school"]
        if not self._check_shape(fact=school_condition.shape,
                                 req=self._required_school_shape):
            raise WrongShapeException(fact=school_condition.shape,
                                      req=self._required_school_shape,
                                      name="Проверка размерности матрицы близости для класса",
                                      aud=self.outer_name)
        self._check_nans(fact=school_condition)
        key, frequency = np.unique(klass_condition.flatten(), return_counts=True)
        # Значения заполненных ячеек
        if not self._check_settings(fact=set(key),
                                    req=self._required_klass_values,
                                    way="<="):
            raise NotEnoughSettings(fact=set(key),
                                    req=self._required_klass_values,
                                    name="Проверка значений в матрице",
                                    way="<=",
                                    aud=self.outer_name)
        school_freq_dict = dict(zip(key, frequency))
        # Участник ровно один
        if not self._check_values_condition(fact=school_freq_dict,
                                            req=self._required_klass_values_condition):
            raise ValuesConditionException(fact=school_freq_dict,
                                           req=self._required_klass_values_condition,
                                           name="Проверка, что в матрице близости для школы ровно один 'Участник'",
                                           aud=self.outer_name)
        # Карта рассадки
        seats_map = raw["seats"]
        # Для нее отлько NaN и значения
        if not self._check_nans(fact=seats_map):      # В данном случае пофиг на размерность
            raise NansInMatrixException(name="Проверка наличия отсутствующих значений в карте рассадки",
                                        aud=self.outer_name)
        # Надо убедиться, что нигде не допущено опечаток
        key, frequency = np.unique(klass_condition.flatten(), return_counts=True)
        if not self._check_settings(fact=set(key),
                                    req=self._required_klass_values,
                                    way="<="):      # Это может оказаться просто пустой лист, на который можно забить
            raise NotEnoughSettings(fact=set(key),
                                    req=self._required_klass_values,
                                    way="<=",
                                    aud=self.outer_name)
        return dict([("settings", settings),
                     ("klass_condition", klass_condition),
                     ("school_condition", school_condition),
                     ("seats_map", seats_map)])

    def __init__(self, raw_settings, outer_name):
        self.outer_name = outer_name
        try:
            settings_dict = self.get_clean_settings(raw_settings)
            self._settings_table = settings_dict["settings"]
            self._settings = settings_dict["settings"]["code"].to_dict()
            self._klass_condition_matrix = settings_dict["klass_condition"]
            self._school_condition_matrix = settings_dict["school_condition"]
            self._seats_map = settings_dict["seats_map"]
        except RassadkaException as e:
            print(e)
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