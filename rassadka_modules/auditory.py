import random
from itertools import product

import numpy as np
import pandas as pd

from rassadka_modules.check_system import Checker
from rassadka_modules.rassadka_exceptions import *
from rassadka_modules.safe_class import SafeClass, Ch


class Seat:
    counter = 0
    total = 0

    def __init__(self, yx, status, data=None, audname=None):
        self.aud = audname
        self.yx = yx
        self.status = bool(status)
        self.data = data
        if status:
            self._plus_total()

    def see_total(self):
        return self.total

    @classmethod
    def count_seated(cls):
        return cls.counter

    @classmethod
    def _plus_total(cls):
        cls.total += 1

    @classmethod
    def _minus_total(cls):
        cls.total -= 1

    @classmethod
    def _plus(cls):
        cls.counter += 1

    @classmethod
    def _minus(cls):
        cls.counter -= 1

    def switch_on(self):
        if not self.status:
            self.status = True
            self._plus_total()
        else:
            raise PermissionError

    def switch_off(self):
        if self.status and self.data is None:
            self.status = False
            self._minus_total()
        else:
            raise PermissionError

    def insert(self, person):
        if not self.status:
            raise BadSeat("Место не задействовано!")
        if self.data is not None:
            raise BadSeat("Место не пусто!")
        self.data = person
        self._plus()

    def remove(self):
        if not self.status:
            raise BadSeat("Место не задействовано!")
        if self.data is None:
            raise BadSeat("Место уже пусто!")
        self._minus()
        self.data = None

    def __bool__(self):             # Тут кто-то сидит?
        return self.data is not None

    def __str__(self):
        return "Ряд {0}; Место {1}".format(*self.yx)

    def __repr__(self):
        res = ";"
        if self.data:
            res = str(self.data["klass"]) + ";"
        return res

    def get_placed(self):
        if self.data:
            res = self.data.copy()
            res["aud"] = self.aud
            res["row"], res["col"] = self.yx
            return res


class Mapping:
    counter = 0

    def __getattr__(self, item):
        where = object.__getattribute__(self, "m")
        return getattr(where, item)

    def __init__(self, boolmatrix, inner_name):
        self.inner_name = inner_name
        res = np.zeros(boolmatrix.shape, dtype=object)
        rows = np.apply_along_axis(lambda row: np.any(row), 1, boolmatrix).cumsum()
        seats = boolmatrix.cumsum(1)     # Получаем места в ряду реальные, накопленные слева направо
        self.available_seats = set()
        self.capacity = 0
        max_row = 0
        max_col = 0
        for y in range(boolmatrix.shape[0]):
            for x in range(boolmatrix.shape[1]):
                res[y, x] = Seat(yx=(int(rows[y]), int(seats[y, x])),
                                 status=boolmatrix[y, x],
                                 audname=self.inner_name)
                if boolmatrix[y, x]:
                    self._plus_capacity((y, x))
                    max_row = max(max_row, y)
                    max_col = max(max_col, x)
        self.m = res[:max_row + 1, :max_col + 1]

    def _plus_capacity(self, yx):
        self.available_seats.add(yx)
        self.capacity += 1

    def _minus_capacity(self, yx):
        self.available_seats.remove(yx)
        self.capacity -= 1

    def _plus(self, yx):
        self.counter += 1
        self.available_seats.remove(yx)

    def _minus(self, yx):
        self.counter -= 1
        self.available_seats.add(yx)

    def switch_off(self, yx):
        try:
            self.m[yx].switch_off()
            self._minus_capacity(yx)
        except PermissionError:
            pass

    def __str__(self):
        return str(self.m)

    def insert(self, yx, data):
        self.m[yx].insert(data)
        self._plus(yx)

    def remove(self, yx):
        self.m[yx].remove()
        self._minus(yx)

    def get_data(self, yx):
        try:
            return self.m[yx].data
        except IndexError:
            return None

    def __getitem__(self, item):
        try:
            return self.m[item]
        except IndexError:
            return None

    def get_all_seated(self):
        res = list()
        for seat in self.m[np.where(self.m)].tolist():
            res.append(seat.get_placed())
        return res

    def clean_all(self):
        for yx in product(range(self.m.shape[0]), range(self.m.shape[1])):
            try:
                self.remove(yx)
            except BadSeat:
                pass

    def get_aud_info(self):
        team_members = 0
        team_num = set()
        klass_count = dict([("n8", 0), ("n9", 0), ("n10", 0), ("n11", 0)])
        for seat in self.m[np.where(self.m)].tolist():
            klass_count["n" + str(seat.data["klass"])] += 1
            if seat.data["team"] != "и":
                team_members += 1
                team_num.add(seat.data["team"])
        res = dict([("team_members", team_members),
                    ("teams", len(team_num)),
                    ("total", self.counter),
                    ("capacity", self.capacity)], **klass_count)
        return res


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
    info_order = ["old_capacity", "capacity", "total", "teams", "team_members",
                  "n8", "n9", "n10", "n11"]

    _required_general_options = {"settings", "seats", "klass", "school"}

    _required_settings_options = {"name", "available", "class_8", "class_9",
                                  "class_10", "class_11", "individual", "command"}

    _required_klass_values = {"far": 'Далеко', "close": 'Рядом', "target": 'Участник'}

    _required_school_values = {"far": 'Далеко', "close": 'Рядом', "target": 'Участник'}

    _required_seats_values = {"seat": 'Место', "not_allowed": 'Проход'}

    _standard_settings_column_names = ["key", "description", "code", "result"]

    _required_klass_values_condition = {_required_klass_values["far"]: Ch(None, None),
                                        _required_klass_values["close"]: Ch(None, None),
                                        _required_klass_values["target"]: Ch(lambda x: x == 1, "== 1")}

    _required_school_values_condition = {_required_school_values["far"]: Ch(None, None),
                                         _required_school_values["close"]: Ch(None, None),
                                         _required_school_values["target"]: Ch(lambda x: x == 1, "== 1")}

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

    # не реализовано
    def _create_paths(self):
        """
        На вход инициализированная карта рассадки,
        на выходе карта в соответствие с
        общепринятыми правилам по созданию
        проходов
        :return: None
        """
        self.old_capacity = self.capacity
        if self.checker.settings["over_row"] != 1:
            trigger = 1
            for row in range(self._seats_map.shape[0]):
                if any([seat.status for seat in self._seats_map[row, :]]):
                    if trigger % self.checker.settings["over_row"] == 0:
                        for seat in range(self._seats_map.shape[1]):
                            self._seats_map.switch_off((row, seat))
                    trigger += 1
                else:
                    trigger = 1
        if self.checker.settings["over_place"] != 1:
            trigger = 1
            for seat in range(self._seats_map.shape[1]):
                if any([seat.status for seat in self._seats_map[:, seat]]):
                    if trigger % self.checker.settings["over_place"] == 0:
                        for row in range(self._seats_map.shape[0]):
                            self._seats_map.switch_off((row, seat))
                    trigger += 1
                else:
                    trigger = 1

    @staticmethod
    def _get_matrix_condition_places(matrix):
        center = np.where(matrix == "target")
        close = np.where(matrix == "close")
        y = close[0] - center[0]      # смещение по у
        x = close[1] - center[1]      # смещение по х
        close = set(zip(y, x))
        return close

    def _debug_message(self, test_name, result):
        end = {True: "Success", False: "Fail"}[result]
        print("{0: >35} for {1: >10} : {2}".format(test_name, self.outer_name, end))

    def _init_settings(self, matrix):
        # Проверяем наличие ошибок неправильного заполнения таблицы свойств
        if not self._check_shape(fact=matrix.shape,
                                 req=self._required_settings_shape):
            raise WrongShapeException(fact=matrix.shape,
                                      req=self._required_settings_shape,
                                      name="Проверка размерности таблицы с настройками аудитории",
                                      aud=self.outer_name)
        if not self._check_nans(fact=matrix):
            raise NansInMatrixException(name="Проверка наличия отсутствующих значений в настройках аудитории",
                                        aud=self.outer_name)
        # Чтобы проверить саму табличку надо проделать несколько махинаций, ведь по умолчанию все в виде матриц
        settings = pd.DataFrame(matrix[1:], columns=matrix[0])
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
        self._settings = settings["code"].to_dict()
        self._settings_table = settings
        self.inner_name = str(self._settings["name"])
        restricted = set()
        for cl in ["class_8", "class_9", "class_10", "class_11"]:
            if not self._settings[cl]:
                restricted.add(cl)
        self.restricted_klasses = restricted

    def _read_klass(self, matrix):
        klass_condition = matrix
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
                                    req=set(self._required_klass_values.values()),
                                    way="<="):
            raise NotEnoughSettings(fact=set(key),
                                    req=set(self._required_klass_values.values()),
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
        klass_condition[klass_condition == self._required_klass_values["far"]] = "far"
        klass_condition[klass_condition == self._required_klass_values["close"]] = "close"
        klass_condition[klass_condition == self._required_klass_values["target"]] = "target"
        klass_yx = self._get_matrix_condition_places(klass_condition)
        return klass_yx

    def _read_school(self, matrix):
        school_condition = matrix
        if not self._check_shape(fact=school_condition.shape,
                                 req=self._required_school_shape):
            raise WrongShapeException(fact=school_condition.shape,
                                      req=self._required_school_shape,
                                      name="Проверка размерности матрицы близости для школы",
                                      aud=self.outer_name)
        self._check_nans(fact=school_condition)
        key, frequency = np.unique(school_condition.flatten(), return_counts=True)
        # Значения заполненных ячеек
        if not self._check_settings(fact=set(key),
                                    req=set(self._required_school_values.values()),
                                    way="<="):
            raise NotEnoughSettings(fact=set(key),
                                    req=set(self._required_school_values.values()),
                                    name="Проверка значений в матрице",
                                    way="<=",
                                    aud=self.outer_name)
        school_freq_dict = dict(zip(key, frequency))
        # Участник ровно один
        if not self._check_values_condition(fact=school_freq_dict,
                                            req=self._required_school_values_condition):
            raise ValuesConditionException(fact=school_freq_dict,
                                           req=self._required_school_values_condition,
                                           name="Проверка, что в матрице близости для школы ровно один 'Участник'",
                                           aud=self.outer_name)
        school_condition[school_condition == self._required_school_values["far"]] = "far"
        school_condition[school_condition == self._required_school_values["close"]] = "close"
        school_condition[school_condition == self._required_school_values["target"]] = "target"
        school_yx = self._get_matrix_condition_places(school_condition)
        return school_yx

    def _init_seats(self, matrix):
        # Карта рассадки
        seats_map = matrix
        # Для нее отлько NaN и значения
        if not self._check_nans(fact=seats_map):      # В данном случае пофиг на размерность
            raise NansInMatrixException(name="Проверка наличия отсутствующих значений в карте рассадки",
                                        aud=self.outer_name)
        # Надо убедиться, что нигде не допущено опечаток
        key, frequency = np.unique(seats_map.flatten(), return_counts=True)
        if not self._check_settings(fact=set(key),
                                    req=set(self._required_seats_values.values()),
                                    way="<="):      # Это может оказаться просто пустой лист, на который можно забить
            raise NotEnoughSettings(fact=set(key),
                                    req=self._required_seats_values,
                                    way="<=",
                                    aud=self.outer_name)
        seats_map[seats_map == self._required_seats_values["seat"]] = True
        seats_map[seats_map == self._required_seats_values["not_allowed"]] = False
        self._seats_map = Mapping(seats_map, str(self._settings["name"]))
        self._create_paths()

    @staticmethod
    def _eval_map_conditions(school, klass):
        """
        Преобразовывает входные диапазоны в вид,
        подготовленный для единообразной проверки
        *пока что буду считать, что там,
        где проверяется школа, должен проверяться и город
        :param school: set
        :param klass: set
        :return: dict {dyx: (check klass?, check school?)}
        """
        klass_school_town = school & klass
        sc_and_town_only = school - klass_school_town
        kl_only = klass - klass_school_town
        res = dict()
        for dyx in klass_school_town:
            res[dyx] = {"klass": True, "school": True, "town": True}
        for dyx in sc_and_town_only:
            res[dyx] = {"klass": False, "school": True, "town": True}
        for dyx in kl_only:
            res[dyx] = {"klass": True, "school": False, "town": False}
        return res

    def __init__(self, raw_settings, outer_name):
        self.checker = Checker()
        self.team_handler = set()
        self.outer_name = outer_name
        try:
            if not self._check_settings(fact=set(raw_settings.keys()),
                                        req=self._required_general_options):
                raise NotEnoughSettings(fact=set(raw_settings.keys()),
                                        req=self._required_general_options,
                                        name="Проверка основных тегов на листе",
                                        aud=self.outer_name)
            self._init_settings(raw_settings["settings"])
            klass_yx = self._read_klass(raw_settings["klass"])
            school_yx = self._read_school(raw_settings["school"])
            self._init_seats(raw_settings["seats"])
            self.klass_school_town_dyx = self._eval_map_conditions(school=school_yx, klass=klass_yx)
        except RassadkaException as e:
            e.log_error()
            raise e

    def __str__(self):
        res = """
            settings:
{0}

            seats_shape: {1}

           klass_school_town
{2}
------------Checker:------------
{3}
""".format(self._settings, self.shape,
           self.klass_school_town_dyx,
           self.checker)
        return res

    def scan(self, yx, person):
        for dyx, todo in self.klass_school_town_dyx.items():
            coord = (yx[0] + dyx[0], yx[1] + dyx[1])
            if not self.checker.compare(one=person,
                                        two=self.get_data(coord),
                                        task=todo):
                return False
        return True

    def __getattr__(self, item):
        where = object.__getattribute__(self, "_seats_map")
        return getattr(where, item)

    def _rand_loop_insert(self, data, available):
        if not available:
            raise EndLoopException
        for_check = random.sample(available, 1)[0]
        available.remove(for_check)
        if self.scan(for_check, data):
            self.insert(for_check, data)
            self.team_handler.add(for_check)
        else:
            self._rand_loop_insert(data, available)

    def rand_insert(self, data):
        # доступна ли аудитория вообще?
        if not self._settings["available"]:
            raise EndLoopException
        # Проверка, можно ли сажать данного участника
        # Критерий "командный/индивидуальный"
        if data["team"] == "и":
            if not self._settings["individual"]:
                raise EndLoopException
        else:
            if not self._settings["command"]:
                raise EndLoopException
        # Критерий по классу
        if data["klass"] in self.restricted_klasses:
            raise EndLoopException
        not_visited = self.available_seats.copy()
        self._rand_loop_insert(data=data, available=not_visited)

    def team_rand_insert(self, team):
        if not self.capacity > 0:
            raise EndLoopException
        # поместится ли команда?
        if self.checker.settings["max_compart"] < (self.counter + len(team)) / self.capacity:
            raise EndLoopException
        # Дальнейшик проверки для простоты находятся во вспомогательной функции
        self.team_handler = set()
        try:
            for member in team:
                self.rand_insert(member)
        except EndLoopException:
            for ups in self.team_handler:
                self.remove(ups)
            # Для конроллера необходимо словить исключение в этом случае
            raise EndLoopException

    def __hash__(self):
        return hash(self.inner_name)

    def __lt__(self, other):
        return self.inner_name < other.inner_name

    def __le__(self, other):
        return self.inner_name <= other.inner_name

    def __gt__(self, other):
        return self.inner_name > other.inner_name

    def __ge__(self, other):
        return self.inner_name >= other.inner_name

    def __eq__(self, other):
        return self.inner_name == other.inner_name

    def info(self):
        info = self.get_aud_info()
        info["name"] = self.inner_name
        info["old_capacity"] = self.old_capacity
        info["av"] = "+" if self._settings["available"] else "-"
        info["com"] = "+" if self._settings["command"] else "-"
        info["ind"] = "+" if self._settings["individual"] else "-"
        info["kl8"] = "+" if self._settings["class_8"] else "-"
        info["kl9"] = "+" if self._settings["class_9"] else "-"
        info["kl10"] = "+" if self._settings["class_10"] else "-"
        info["kl11"] = "+" if self._settings["class_11"] else "-"
        return info

    def summary(self):
        message = """
Аудитрия [{av}] {name}
Доступность: K[{com}], И[{ind}]
Всего мест:         {capacity: <3}| 8  класс[{kl8}]:{n8}
Посажено:           {total: <3}| 9  класс[{kl9}]:{n9}
Из них командных:   {team_members: <3}| 10 класс[{kl10}]:{n10}
Всего команд:       {teams: <3}| 11 класс[{kl11}]:{n11}
""".format(**self.info())
        return message

    def __repr__(self):
        mes = "<{0}: cap={1}>"
        return mes.format(self.inner_name, self.capacity)

    def map_with_data_to_writer(self, writer, name_format, data):
        dy = 1
        dx = 0
        writer.write(0, 0, self.inner_name, name_format)
        writer.write(0 + dy, 0 + dx, "Абсолютные")
        for y in range(self.shape[0]):
            writer.write(y + 1 + dy, 0 + dx, "ряд " + str(y + 1))
        for x in range(self.shape[1]):
            writer.write(0 + dy, x + 1 + dx, "место " + str(x + 1))
        for y, x in product(range(self.shape[0]), range(self.shape[1])):
            task = self.get_data((y + dy, x + dx))
            if task:
                task = task[data]
            writer.write(y + 1 + dy, x + 1 + dx, task)

    def map_with_status_to_writer(self, writer, name_format):
        dy = 1
        dx = 0
        writer.write(0, 0, self.inner_name, name_format)
        writer.write(0 + dy, 0 + dx, "Абсолютные")
        for y in range(self.shape[0]):
            writer.write(y + 1 + dy, 0 + dx, "ряд " + str(y + 1))
        for x in range(self.shape[1]):
            writer.write(0 + dy, x + 1 + dx, "место " + str(x + 1))
        for y, x in product(range(self.shape[0]), range(self.shape[1])):
            task = "проход"
            if self._seats_map[y, x].status:
                task = str(self._seats_map[y, x].yx)
            writer.write(y + 1 + dy, x + 1 + dx, task)

    def people_table(self):
        table = pd.DataFrame.from_records(self.get_all_seated())
        return table

if __name__ == "__main__":
    pass
