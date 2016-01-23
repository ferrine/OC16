import pickle
import random
import numpy as np
import pandas as pd
import xlsxwriter

from pandas import ExcelFile
from collections import OrderedDict as oDict
from rassadka_modules.auditory import Auditory, Seat
from rassadka_modules.check_system import Checker
from rassadka_modules.common import clr, swap, mutable
from rassadka_modules.excelprocessor.reader import splitter
from rassadka_modules.rassadka_exceptions import *
from rassadka_modules.safe_class import SafeClass


class Controller(SafeClass):
    _required_input_cols = oDict([("email", "email"), ("fam", "Фамилия"), ("name", "Имя"), ("otch", "Отчество"),
                                 ("town", "Город"), ("school", "Школа"), ("team", "Команда"),
                                 ("klass", "Класс")])
    _default_full_dict = _required_input_cols.copy()
    _default_full_dict.update([("aud", "Аудитория"), ("row", "Ряд"), ("col", "Место")])
    max_iter = 20

    def __init__(self, file, from_pickle=False):
        if from_pickle:
            data = pickle.load(file)
            Checker.clean_global_init(data["checker_meta"])
            Seat.counters = data["seats_meta"]
            self.__dict__.update(data["controller"].__dict__)
            return
        self.mode = "None"
        self.key_holder = set()
        self.last_change = None
        self.people = pd.DataFrame()
        self.auds = dict()
        self.inds = list()
        self.teams = list()
        self.seed = 1
        found_main_settings = False
        excel_file = ExcelFile(file)
        for name in excel_file.sheet_names:
            raw_frame = excel_file.parse(name, index_col=None, header=None)
            unresolved_dict = splitter(raw_frame, named=True)
            if "main_settings" in unresolved_dict.keys():
                if found_main_settings:
                    print("Две страницы с общими настройками!")
                    continue
                found_main_settings = True
                Checker.raw_global_init(unresolved_dict)
                self.checker = Checker()
        if not found_main_settings:
            raise TypeError("Настройки не найдены, на странице с настройками нужен ключ main_settings")
        for name in excel_file.sheet_names:
            raw_frame = excel_file.parse(name, index_col=None, header=None)
            unresolved_dict = splitter(raw_frame, named=True)
            if "main_settings" not in unresolved_dict.keys():
                tmp = Auditory(unresolved_dict, outer_name=name)
                if tmp.inner_name in self.auds.keys():
                    raise TypeError("Есть одинаковые аудитории")
                else:
                    self.auds[tmp.inner_name] = tmp

    def _rand_loop_insert(self, data, available):
        if not available:
            raise NoFreeAuditory
        for_check = random.sample(available, 1)[0]
        available.remove(for_check)
        try:
            for_check.rand_insert(data)
        except EndLoopException:
            self._rand_loop_insert(data, available)

    def _rand_loop_team_insert(self, data, available):
        if not available:
            raise NoFreeAuditory
        for_check = random.sample(available, 1)[0]
        available.remove(for_check)
        try:
            for_check.team_rand_insert(data)
        except EndLoopException:
            self._rand_loop_team_insert(data, available)

    @mutable
    def rand_aud_insert(self, data):
        not_visited = set(self.auds.values())
        self._rand_loop_insert(data=data, available=not_visited)

    @mutable
    def rand_aud_team_insert(self, data):
        not_visited = set(self.auds.values())
        self._rand_loop_team_insert(data=data, available=not_visited)

    @mutable
    def _split_people(self):
        tmp = self.people.drop(["aud", "row", "col"], errors="ignore", axis=1)
        self.inds = tmp.query("team == 'и'").to_dict(orient="records")
        if not self.checker.settings["com_in_one"]:
            self.inds.extend(tmp.query("team != 'и'").to_dict(orient="records"))
        else:
            for team_number in list(np.unique(tmp.query("team != 'и'")["team"])):
                query = "team == " + str(team_number)
                self.teams.append(tmp.query(query).to_dict(orient="records"))

    @mutable
    def load_people(self, file):
        self.inds = list()
        self.teams = list()
        people = pd.read_excel(file, sheetname=0).applymap(clr)
        if not self._check_settings(fact=set(people.columns),
                                    req=set(self._required_input_cols.values()),
                                    way=">="):
            raise NotEnoughSettings(fact=set(people.columns),
                                    req=set(self._required_input_cols.values()),
                                    way=">=")
        people = people.rename(columns=swap(self._default_full_dict))
        if (any([item in people.columns for item in ["aud", "row", "col"]]) and
           not all([item in people.columns for item in ["aud", "row", "col"]])):
            raise ControllerException("Некорректно заданы столбцы с местами")
        if len(people) == 0:
            self.mode = "None"
            return
        elif "aud" in people.columns:
            self.mode = "edit"
        else:
            self.mode = "input"
        people["klass"] = people["klass"]
        self.people = people
        self._split_people()

    @mutable
    def clean_all(self):
        for aud in self.auds.values():
            aud.clean_all()

    @mutable
    def lock_all(self, key):
        for aud in self.auds.values():
            aud.lock_all(key)
        self.key_holder.add(key)

    @mutable
    def unlock_all(self, key):
        if key in self.key_holder:
            for aud in self.auds.values():
                aud.unlock_all(key)
            self.key_holder.remove(key)
        else:
            raise KeyError(key)

    @mutable
    def update_all(self, forced=False):
        if not self.mode == "edit":
            raise ControllerException("PermissionError")
        for new_data in self.people.to_dict(orient="records"):
            for_insert = new_data.copy()
            del for_insert["aud"], for_insert["row"], for_insert["col"]
            self.auds[new_data["aud"]].update_by_position((new_data["row"], new_data["col"]), for_insert, forced=forced)

    @mutable
    def selected_remove(self):
        if not self.mode == "edit":
            raise ControllerException("PermissionError")
        for remove_data in self.people.to_dict(orient="records"):
            self.auds[remove_data["aud"]].remove_by_position((remove_data["row"], remove_data["col"]))

    @mutable
    def erase_loaded_people(self):
        self.people = pd.DataFrame()
        self.inds = list()
        self.teams = list()
        self.mode = "None"

    @mutable
    def place_them(self):
        if len(self.people) and len(self.seated_people):
            if (set(self.people["email"])) & set(self.seated_people["email"]):
                message = "{} загруженных участников рассажены!"
                message = message.format(len(set(self.people["email"]) & set(self.seated_people["email"])))
                raise ControllerException(message)
        random.seed(self.seed)
        try:
            for team in self.teams:
                self.rand_aud_team_insert(team)
            for individual in self.inds:
                self.rand_aud_insert(individual)
        except NoFreeAuditory:
            self.clean_all()
            if self.seed <= self.max_iter:
                self.seed += 1
                self.place_them()
            else:
                raise NoFreeAuditory("{0} итераций были безуспешны, слишком мало аудиторий".format(self.max_iter))

    @property
    def seated_people(self):
        seated = list()
        for aud in sorted(self.auds.values()):
                seated.extend(aud.get_all_seated())
        frame = pd.DataFrame.from_dict(seated)
        return frame

    def whole_summary(self):
        message = ""
        for aud in sorted(self.auds.values()):
            message += aud.summary() + "\n"
        return message

    def xlsx_summary(self, file):
        with pd.ExcelWriter(file) as writer:
            summary = list()
            for aud in self.auds.values():
                summary.append(aud.info())
            table = pd.DataFrame.from_records(summary, index="name")
            table.ix[:, Auditory.export_names.keys()].rename(columns=Auditory.export_names).to_excel(writer)

    def dump_seated(self, file, full=False):
        with pd.ExcelWriter(file) as writer:
            if not full:
                select = ["fam", "name", "otch", "aud", "row", "col"]
            else:
                select = list(self._default_full_dict.keys())
            frame = self.seated_people
            frame.ix[:, select].sort_values("fam", ascending=True).rename(columns=self._default_full_dict).to_excel(writer, index=False)

    def write_maps_with_data(self, file, data):
        with xlsxwriter.Workbook(file) as workbook:
            form = workbook.add_format()
            form.set_font_size(30)
            form.set_bold()
            for aud in self.auds.values():
                sheet = workbook.add_worksheet(aud.inner_name)
                aud.map_with_data_to_writer(sheet, form, data)

    def write_maps_with_status(self, file):
        with xlsxwriter.Workbook(file) as workbook:
            form = workbook.add_format()
            form.set_font_size(30)
            form.set_bold()
            for aud in self.auds.values():
                sheet = workbook.add_worksheet(aud.inner_name)
                aud.map_with_status_to_writer(sheet, form)

    def to_pickle(self, file):
        prepared = dict([("checker_meta", Checker.settings),
                         ("seats_meta", Seat.counters),
                         ("controller", self)])
        pickle.dump(prepared, file)

    @property
    def info(self):
        info = dict()
        info["last_change"] = self.last_change
        info["n_auds"] = len(self.auds)
        info["n_used_auds"] = sum([aud.settings["available"] for aud in self.auds.values()])
        info["seated"] = Seat.counters["seated"]
        info["seats_total"] = Seat.counters["total"]
        info["people"] = len(self.people)
        info["n_teams"] = len(self.teams)
        return info

    def __str__(self):
        message = """
Последнее изменение {last_change}
Всего аудиторий {n_used_auds}({n_auds: 4})
Загружено {people} человек, {n_teams} команд
Всего мест {seats_total}, посажено {seated}
        """.format(**self.info)
        return message

    def seat_by_position(self, seat):
        if not isinstance(seat["row"], int) and isinstance(seat["col"], int):
            raise ControllerException("Место/Ряд должны быть числами")
        return self.auds[str(seat["aud"])].real_seats[(seat["row"], seat["col"])]
