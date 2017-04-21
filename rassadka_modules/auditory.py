import random
import numpy as np
import pandas as pd

from itertools import product
from rassadka_modules.check_system import Checker
from rassadka_modules.rassadka_exceptions import *
from rassadka_modules.safe_class import SafeClass
from rassadka_modules.common import Ch
from collections import OrderedDict as oDict


class Seat:
    counters = dict([("seated", 0),
                     ("arrived", 0)])

    def __init__(self, yx, status, data=None, audname=None):
        self.locked = False
        self.lock_key = None
        self.aud = audname
        self.yx = yx
        self.status = bool(status)
        self.meta_status = status
        self.data = data if data else dict()

    def __bool__(self):             # Тут кто-то сидит?
        return bool(self.data)

    def __str__(self):
        return "Ряд {0}; Место {1}".format(*self.yx)

    def __repr__(self):
        res = ";"
        if self.data:
            res = str(self.data["klass"]) + ";"
        return res

    @classmethod
    def _plus_seated(cls):
        cls.counters["seated"] += 1

    @classmethod
    def _minus_seated(cls):
        cls.counters["seated"] -= 1

    @classmethod
    def _plus_arrived(cls):
        cls.counters["arrived"] += 1

    @classmethod
    def _minus_arrived(cls):
        cls.counters["arrived"] -= 1

    @classmethod
    def total_seated(cls) -> int:
        return cls.counters["seated"]

    @classmethod
    def total_arrived(cls) -> int:
        return cls.counters["arrived"]

    def switch_on(self):
        if not self.status:
            self.status = True
        else:
            raise PermissionError

    def switch_off(self):
        if self.status and not self.data:
            self.status = False
        else:
            raise PermissionError

    def insert(self, person):
        if not self.status:
            raise BadSeat("Место не задействовано!")
        if self.data:
            raise BadSeat("Место не пусто!")
        self.data = person
        if self.data.get("arrived"):
            self._minus_arrived()
        self.data["arrived"] = False
        self._plus_seated()

    def remove(self):
        if self.locked:
            raise BadSeat("Место заблокировано!")
        if not self.status:
            raise BadSeat("Место не задействовано!")
        if not self.data:
            raise BadSeat("Место уже пусто!")
        self._minus_seated()
        if self.data.get("arrived"):
            self._minus_arrived()
        self.data = dict()

    def lock(self, key, change=False):
        if not self.data:
            return
        if not self.locked:
            self.locked = True
            self.lock_key = key
        elif change:
            self.lock_key = key

    def unlock(self, key=None, forced=False):
        if not key and forced:
            self.locked = False
            self.lock_key = None
        elif self.locked and key == self.lock_key:
            self.locked = False
            self.lock_key = None

    def arrived(self):
        if not self:
            raise PermissionError
        if not self.data["arrived"] == True:
            self.data["arrived"] = True
            self._plus_arrived()

    def arrived_del(self):
        if not self:
            raise PermissionError
        if self.data["arrived"]:
            self.data["arrived"] = False
            self._minus_arrived()

    def update(self, new_data, forced):
        if not self.status:
            raise ControllerException("Permission to {0} {1} {2} denied".format(self.aud, *self.yx))
        if self.locked and not forced:
            raise ControllerException("Permission to {0} {1} {2} denied".format(self.aud, *self.yx))
        if new_data.get("arrived", False) and not self.data.get("arrived", False):
            self._plus_arrived()
        elif not new_data.get("arrived", False) and self.data.get("arrived", False):
            self._minus_arrived()
        self.data = new_data
        if "arrived" not in self.data.keys():
            self.data["arrived"] = False

    def get_placed(self) -> dict:
        if self.data:
            res = self.data.copy()
            res["aud"] = self.aud
            res["row"], res["col"] = self.yx
            res["key"] = self.lock_key
            return res


class Mapping:
    def __getitem__(self, item) -> Seat:
        try:
            return self.m[item]
        except IndexError:
            return None

    def __getattr__(self, item):
        where = object.__getattribute__(self, "m")
        return getattr(where, item)

    def __init__(self, meta_status_matrix, inner_name):
        self.counter = 0
        self.inner_name = inner_name
        self.available_seats = set()
        self.capacity = 0
        self.coords_to_yx = dict()
        res = np.zeros(meta_status_matrix.shape, dtype=object)
        rows = np.apply_along_axis(np.any, 1, meta_status_matrix).cumsum()
        seats = np.vectorize(bool)(meta_status_matrix).cumsum(1)     # Получаем места в ряду реальные,
        max_row = 0                                                  # накопленные слева направо
        max_col = 0
        for y in range(meta_status_matrix.shape[0]):
            for x in range(meta_status_matrix.shape[1]):
                coords = (int(rows[y]), int(seats[y, x]))
                res[y, x] = Seat(yx=coords,
                                 status=meta_status_matrix[y, x],
                                 audname=self.inner_name)
                if meta_status_matrix[y, x]:
                    self.coords_to_yx[coords] = (y, x)
                    self._plus_capacity((y, x))
                    max_row = max(max_row, y)
                    max_col = max(max_col, x)
        self.m = res[:max_row + 1, :max_col + 1]

    def __str__(self):
        return str(self.m)

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

    def switch_off_by_yx(self, yx):
        try:
            self.m[yx].switch_off()
            self._minus_capacity(yx)
        except PermissionError:
            pass

    def insert(self, yx, data):
        self.m[yx].insert(data)
        self._plus(yx)

    def update(self, yx, new_data, forced):
        self.m[yx].update(new_data, forced)

    def remove(self, yx):
        self.m[yx].remove()
        self._minus(yx)

    def lock(self, yx, key):
        self.m[yx].lock(key)

    def unlock(self, yx, key=None, forced=False):
        self.m[yx].unlock(key, forced)

    def lock_by_coords(self, coords, key):
        self.lock(self.coords_to_yx[coords], key)

    def unlock_by_coords(self, coords):
        self.unlock(self.coords_to_yx[coords], forced=True)

    def update_by_coords(self, coords, new_data, forced=False):
        if self.m[self.coords_to_yx[coords]]:
            self.update(self.coords_to_yx[coords], new_data, forced)
        else:
            self.insert(self.coords_to_yx[coords], new_data)

    def remove_by_coords(self, coords):
        self.remove(self.coords_to_yx[coords])

    def get_data(self, yx) -> dict:
        try:
            return self.m[yx].data
        except IndexError:
            return dict()

    def get_all_seated(self) -> list:
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

    def lock_all(self, key):
        for yx in product(range(self.m.shape[0]), range(self.m.shape[1])):
            try:
                self.lock(yx, key)
            except BadSeat:
                pass

    def unlock_all(self, key):
        for yx in product(range(self.m.shape[0]), range(self.m.shape[1])):
            try:
                self.unlock(yx, key)
            except BadSeat:
                pass

    @property
    def teams_set(self) -> set:
        team_num = set()
        for seat in self.m[np.where(self.m)].tolist():
            if seat.data["team"] != "и":
                team_num.add(seat.data["team"])
        return team_num

    @property
    def keys(self) -> list:
        keys = list()
        for seat in self.m[np.where(self.m)].tolist():
            if seat.lock_key:
                keys.append(seat.lock_key)
        return keys

    @property
    def teams_arrived_set(self) -> set:
        team_num_arrived = set()
        for seat in self.m[np.where(self.m)].tolist():
            if seat.data["team"] != "и" and seat.data["arrived"]:
                team_num_arrived.add(seat.data["team"])
        return team_num_arrived

    @property
    def mapping_info(self) -> dict:
        arrived = 0
        team_members = 0
        team_members_arrived = 0
        klass_count = dict([("n8", 0), ("n9", 0), ("n10", 0), ("n11", 0),
                            ("n8_a", 0), ("n9_a", 0), ("n10_a", 0), ("n11_a", 0)])
        for seat in self.m[np.where(self.m)].tolist():
            klass_count["n" + str(seat.data["klass"])] += 1
            if seat.data["arrived"]:
                klass_count["n" + str(seat.data["klass"]) + "_a"] += 1
                arrived += 1
                if seat.data["team"] != "и":
                    team_members_arrived += 1
            if seat.data["team"] != "и":
                team_members += 1
        res = dict([("team_members", team_members),
                    ("teams", len(self.teams_set)),
                    ("total", self.counter),
                    ("capacity", self.capacity),
                    ("arrived", arrived),
                    ("team_members_arrived", team_members_arrived),
                    ("teams_arrived", len(self.teams_arrived_set))], **klass_count)
        return res

    def mark_arrival_by_coords(self, coords):
        self.m[self.coords_to_yx[coords]].arrived()
        self.lock(self.coords_to_yx[coords], "arrival")

    def coords_by_email_in_aud(self, email) -> dict:
        for person in self.get_all_seated():
            if person["email"] == email:
                res = {key: value for key, value in person.items() if key in ["aud", "row", "col"]}
                return res
        raise KeyError


class Auditory(SafeClass):

    CHECK = ["available", "class_8", "class_9",             # Для виджета
             "class_10", "class_11", "individual", "command"]
    export_names = oDict([("old_capacity", "Вместительность"), ("capacity", "Вместительность с доп проходами"),
                          ("total", "Сидит"), ("arrived", "Сидит(+)"),
                          ("teams", "Команд"), ("teams_arrived", "Команд(+)"),
                          ("team_members", "Командников"), ("team_members_arrived", "Командников(+)"),
                          ("n8", "8кл"), ("n8_a", "8кл(+)"),
                          ("n9", "9кл"), ("n9_a", "9кл(+)"),
                          ("n10", "10кл"), ("n10_a", "10кл(+)"),
                          ("n11", "11кл"), ("n11_a", "11кл(+)")])

    _required_general_options = {"settings", "seats", "klass", "school"}

    _required_settings_options = {"name", "available", "class_8", "class_9",
                                  "class_10", "class_11", "individual", "command",
                                  "over_place", "over_row"}

    _required_klass_values = {"far": 'Далеко', "close": 'Рядом', "target": 'Участник'}

    _required_school_values = {"far": 'Далеко', "close": 'Рядом', "target": 'Участник'}

    _required_seats_values = {"seat": 'Место', 'fake_seat': 'Не Место', "not_allowed": 'Проход'}

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
                                           "command": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
                                           "over_place": Ch(lambda x: x in {1, 2}, "in {1, 2}"),
                                           "over_row": Ch(lambda x: x in {1, 2, 3}, "in {1, 2, 3}")}

    _required_klass_shape = (7, 7)

    _required_school_shape = (7, 7)

    _required_seats_shape = None

    _required_settings_shape = (11, 4)

    def _create_paths(self):
        self.old_capacity = self.map.capacity
        if self.settings["over_row"] != 1:
            trigger = 1
            for row in range(self.map.shape[0]):
                if any([seat.status for seat in self.map[row, :]]):
                    if trigger % self.settings["over_row"] == 0:
                        for seat in range(self.map.shape[1]):
                            self.map.switch_off_by_yx((row, seat))
                    trigger += 1
                else:
                    trigger = 1
        if self.settings["over_place"] != 1:
            trigger = 1
            for seat in range(self.map.shape[1]):
                if any([seat.status for seat in self.map[:, seat]]):
                    if trigger % self.settings["over_place"] == 0:
                        for row in range(self.map.shape[0]):
                            self.map.switch_off_by_yx((row, seat))
                    trigger += 1
                else:
                    trigger = 1
        # тут убираются те места, которые мы исключили сами
        for yx in product(range(self.map.shape[0]), range(self.map.shape[1])):
            if self.map[yx].meta_status == 2:
                self.map.switch_off_by_yx(yx)

    @staticmethod
    def _get_matrix_condition_places(matrix) -> set:
        """
        :type matrix: np.matrix
        :return:
        """
        center = np.where(matrix == "target")
        close = np.where(matrix == "close")
        y = close[0] - center[0]      # смещение по у
        x = close[1] - center[1]      # смещение по х
        close = set(zip(y, x))
        return close

    def _init_settings_from_dict(self, settings):
        self.settings = settings
        self.inner_name = str(self.settings["name"])
        restricted = set()
        for cl in ["class_8", "class_9", "class_10", "class_11"]:
            if not self.settings[cl]:
                restricted.add(cl)
        self.restricted_klasses = restricted

    def _init_settings(self, matrix):
        """
        :type matrix: np.matrix
        :return:
        """
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
        self._init_settings_from_dict(settings["code"].to_dict())

    def _read_klass(self, matrix) -> set:
        """
        :type matrix: np.matrix
        :return:
        """
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

    def _read_school(self, matrix) -> set:
        """
        :type matrix: np.matrix
        :return:
        """
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
        """
        :type matrix: np.matrix
        :return:
        """
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
                                    req=set(self._required_seats_values.values()),
                                    way="<=",
                                    aud=self.outer_name)
        seats_map[seats_map == self._required_seats_values["seat"]] = 1
        seats_map[seats_map == self._required_seats_values["fake_seat"]] = 2
        seats_map[seats_map == self._required_seats_values["not_allowed"]] = 0
        seats_map = seats_map.astype(np.int32, copy=False)
        self.map = Mapping(seats_map, str(self.settings["name"]))
        self._create_paths()

    @staticmethod
    def _eval_map_conditions(school, klass) -> dict:
        """
        Преобразовывает входные диапазоны в вид,
        подготовленный для единообразной проверки
        *пока что буду считать, что там,
        где проверяется школа, должен проверяться и город
        :type school: set
        :type klass: set
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
        """
        :param raw_settings: dict
        :param outer_name: str
        :return:
        """
        self.checker = Checker()
        self.team_handler = set()
        self.outer_name = outer_name

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

    def _rand_loop_insert(self, data, available):
        """
        :type data: dict
        :type available: set
        :return:
        """
        if not available:
            raise EndLoopException
        for_check = random.sample(available, 1)[0]
        available.remove(for_check)
        if self._scan(for_check, data):
            self.map.insert(for_check, data)
            self.team_handler.add(for_check)
        else:
            self._rand_loop_insert(data, available)

    def _scan(self, yx, person) -> bool:
        """
        :type yx: (int, int)
        :type person: dict
        :return:
        """
        for dyx, todo in self.klass_school_town_dyx.items():
            coord = (yx[0] + dyx[0], yx[1] + dyx[1])
            if not self.checker.compare(one=person,
                                        two=self.map.get_data(coord),
                                        task=todo):
                return False
        return True

    def __getattr__(self, item):
        where = object.__getattribute__(self, "map")
        return getattr(where, item)

    def __repr__(self):
        res = "<{name}[{av}]:{capacity}({total})>".format(**self.info)
        return res

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

    @property
    def info(self) -> dict:
        info = self.map.mapping_info
        info["name"] = self.inner_name
        info["old_capacity"] = self.old_capacity
        info["av"] = "+" if self.settings["available"] else "-"
        info["com"] = "+" if self.settings["command"] else "-"
        info["ind"] = "+" if self.settings["individual"] else "-"
        info["kl8"] = "+" if self.settings["class_8"] else "-"
        info["kl9"] = "+" if self.settings["class_9"] else "-"
        info["kl10"] = "+" if self.settings["class_10"] else "-"
        info["kl11"] = "+" if self.settings["class_11"] else "-"
        return info

    @property
    def summary(self) -> str:
        message = """
Аудитрия [{av}] {name}
Доступность: K[{com}], И[{ind}]
Всего мест:         {capacity: <3}     | 8  класс[{kl8}]:{n8:<3}({n8_a})
Посажено:           {total: <3}({arrived:<3})| 9  класс[{kl9}]:{n9:<3}({n9_a})
Из них командных:   {team_members: <3}({team_members_arrived:<3})| 10 класс[{kl10}]:{n10:<3}({n10_a})
Всего команд:       {teams: <3}({teams_arrived:<3})| 11 класс[{kl11}]:{n11:<3}({n11_a})
""".format(**self.info)
        return message

    @property
    def people_table(self) -> pd.DataFrame:
        table = pd.DataFrame.from_records(self.map.get_all_seated())
        return table

    def rand_insert(self, data):
        """
        :type data: dict
        :return:
        """
        # доступна ли аудитория вообще?
        if not self.settings["available"]:
            raise EndLoopException
        # Проверка, можно ли сажать данного участника
        # Критерий "командный/индивидуальный"
        if data["team"] == "и":
            if not self.settings["individual"]:
                raise EndLoopException
        else:
            if not self.settings["command"]:
                raise EndLoopException
        # Критерий по классу
        if data["klass"] in self.restricted_klasses:
            raise EndLoopException
        not_visited = self.map.available_seats.copy()
        self._rand_loop_insert(data=data, available=not_visited)

    def rand_insert_team(self, team):
        """
        :type team: list
        :return:
        """
        if not self.map.capacity > 0:
            raise EndLoopException
        # поместится ли команда?
        if self.checker.settings["max_compart"] < (self.map.counter + len(team)) / self.old_capacity:
            raise EndLoopException
        # Дальнейшик проверки для простоты находятся во вспомогательной функции
        self.team_handler = set()
        try:
            for member in team:
                self.rand_insert(member)
        except EndLoopException:
            for ups in self.team_handler:
                self.map.remove(ups)
            # Для конроллера необходимо словить исключение в этом случае
            raise EndLoopException

    def map_with_data_to_writer(self, writer, seats_format, data, reverse=True):
        writer.write(0, 0, "Абс.")
        y_range = range(self.map.shape[0])
        x_range = range(self.map.shape[1])
        if reverse:
            y_zip = list(zip(y_range, reversed(y_range)))
            x_zip = list(zip(x_range, reversed(x_range)))
        else:
            y_zip = list(zip(y_range, y_range))
            x_zip = list(zip(x_range, x_range))
        yx_zip = product(y_zip, x_zip)
        for y, wy in y_zip:
            writer.write(wy + 1, 0, "ряд " + str(y + 1))
        for x, wx in x_zip:
            writer.write(0, wx + 1, "мст " + str(x + 1))
        for (y, wy), (x, wx) in yx_zip:
            person = self.map.get_data((y, x))
            if self.map.m[(y, x)]:
                task = str(person.get(data, 'None'))
            elif self.map.m[(y, x)].status:
                task = "..."
            else:
                task = "______"
            writer.write(wy + 1, wx + 1, task, seats_format)
        writer.write(self.map.shape[0] + 2, 0, "ДОСКА ВНИЗУ" if reverse else "ДОСКА ВВЕРХУ")

    def map_with_status_to_writer(self, writer, seats_format, reverse=True):
        writer.write(0, 0, "Абс.")
        y_range = range(self.map.shape[0])
        x_range = range(self.map.shape[1])
        if reverse:
            y_zip = list(zip(y_range, reversed(y_range)))
            x_zip = list(zip(x_range, reversed(x_range)))
        else:
            y_zip = list(zip(y_range, y_range))
            x_zip = list(zip(x_range, x_range))
        yx_zip = product(y_zip, x_zip)
        for y, wy in y_zip:
            writer.write(wy + 1, 0, "ряд " + str(y + 1))
        for x, wx in x_zip:
            writer.write(0, wx + 1, "мст " + str(x + 1))
        for (y, wy), (x, wx) in yx_zip:
            task = "______"
            if self.map[y, x].status:
                task = str(self.map[y, x].yx)
            writer.write(wy + 1, wx + 1, task, seats_format)
        writer.write(self.map.shape[0] + 2, 0, "ДОСКА ВНИЗУ" if reverse else "ДОСКА ВВЕРХУ")

    def switch_on(self):
        if self.settings["available"] != 1:
            self.settings["available"] = 1

    def switch_off(self):
        if self.settings["available"] != 0:
            self.settings["available"] = 0

    def __del__(self):
        Seat.counters["seated"] -= self.info["total"]
        Seat.counters["arrived"] -= self.info["arrived"]

    def refresh(self, new_settings):
        self.settings.update(new_settings)
        self._init_settings_from_dict(self.settings)

if __name__ == "__main__":
    pass
