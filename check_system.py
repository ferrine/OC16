from safe_class import SafeClass, Ch
from rassadka_exceptions import *
import pandas as pd
from itertools import product, permutations


class Checker(SafeClass):
    outer_name = "Основные настройки"
    _pre_inited = False
    _settings = None
    _settings_table = None

    _required_general_options = {"main_settings"}

    _required_settings_shape = (14, 4)

    _required_settings_options = {"over_place", "over_row", "cl8_9",
                                  "cl8_10", "cl8_11", "cl9_10",
                                  "cl9_11", "cl10_11", "one_school",
                                  "one_town", "com_in_one", "max_compart",
                                  "debug_mode"}

    kl_comb_names = {"cl8_9": (8, 9), "cl8_10": (8, 10),
                     "cl8_11": (8, 11), "cl9_10": (9, 10),
                     "cl9_11": (9, 11), "cl10_11": (10, 11)}

    _standard_settings_column_names = ["key", "description", "code", "result"]

    _required_settings_values_condition = {"over_place": Ch(lambda x: x in {1, 2}, "in {1, 2}"),
                                           "over_row": Ch(lambda x: x in {1, 2, 3}, "in {1, 2, 3}"),
                                           "cl8_9": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "cl8_10": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "cl8_11": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "cl9_10": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "cl10_11": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "one_school": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "one_town": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "com_in_one": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "max_com_part": Ch(lambda x: 0 <= x <= 1, "0 <= x <= 1"),
                                           "debug_mode": Ch(lambda x: x in {1, 0}, "in {0, 1}")}

    @classmethod
    def _eval_klass_conditions(cls):
        all_klasses = set(product([8, 9, 10, 11], repeat=2))
        allowed = set()
        for name, item in cls.kl_comb_names.items():
            if cls._settings[name]:
                allowed |= set(permutations(item))
        restricted = all_klasses - allowed
        cls.restricted_klasses = restricted


    @classmethod
    def _init_settings(cls, matrix):
        # Проверяем наличие ошибок неправильного заполнения таблицы свойств
        if not cls._check_shape(fact=matrix.shape,
                                req=cls._required_settings_shape):
            raise WrongShapeException(fact=matrix.shape,
                                      req=cls._required_settings_shape,
                                      name="Проверка размерности таблицы с общими настройками",
                                      aud=cls.outer_name)
        if not cls._check_nans(fact=matrix):
            raise NansInMatrixException(name="Проверка наличия отсутствующих значений в общих настройках",
                                        aud=cls.outer_name)
        # Чтобы проверить саму табличку надо проделать несколько махинаций, ведь по умолчанию все в виде матриц
        settings = pd.DataFrame(matrix[1:], columns=matrix[0])
        settings.columns = cls._standard_settings_column_names
        settings.set_index("key", inplace=True)
        # Проверяем все ли настнойки внесены в табличку
        if not cls._check_settings(fact=set(settings.index),
                                   req=cls._required_settings_options):
            raise NotEnoughSettings(fact=set(settings.index),
                                    req=cls._required_settings_options,
                                    name="Проверка вхождения всех необходимых\
переменных по ключу в общих настройках",
                                    aud=cls.outer_name)
        # Проверяем, что это именно то, что мы ожидали получить на входе
        if not cls._check_values_condition(fact=settings["code"].to_dict(),
                                           req=cls._required_settings_values_condition):
            raise ValuesConditionException(fact=settings["code"].to_dict(),
                                           req=cls._required_settings_values_condition,
                                           name="Проверка валидности ввода настроек в таблицу с общими настройками",
                                           aud=cls.outer_name)
        cls._settings = settings["code"].to_dict()
        cls._settings_table = settings

    @classmethod
    def pre_init(cls, raw_settings):
        try:
            if not cls._check_settings(fact=set(raw_settings.keys()),
                                       req=cls._required_general_options):
                raise NotEnoughSettings(fact=set(raw_settings.keys()),
                                        req=cls._required_general_options,
                                        name="Проверка основных тегов на листе",
                                        aud=cls.outer_name)
            cls._init_settings(raw_settings["main_settings"])
            cls._eval_klass_conditions()
        except RassadkaException as e:
            print(e)
            e.logerror()
        cls._pre_inited = True

    def __init__(self):
        assert self._pre_inited is True, "Настройки не инициализированы"

    def __str__(self):
        res = """
            main_settings:
{0}
""".format(self._settings)
        return res

    def compare(self, one, two, task):
        """
        Проверка двух экзембляров
        :param one:
        :param two:
        :param task:    (check klass?, check school?)
        :return: bool
        """
        if one is None or two is None:
            return True

        res = True
        # Проверяем, могут ли классы сидеть вместе
        if task[0]:         # первая позиция отвечает за класс
            res &= (one["klass"], two["klass"]) not in self.restricted_klasses
        if task[1]:         # вторая позиция за школу
            res &= not one["school"] == two["school"]
        # тут мог бы быть код про города
        #
        return res
