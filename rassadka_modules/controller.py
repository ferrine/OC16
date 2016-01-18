import pickle
import random
import numpy as np
import pandas as pd
import xlsxwriter

from pandas import ExcelFile
from rassadka_modules.auditory import Auditory, Seat
from rassadka_modules.check_system import Checker
from rassadka_modules.common import clr, get_numbers, swap, mutable
from rassadka_modules.excelprocessor.reader import splitter
from rassadka_modules.rassadka_exceptions import *
from rassadka_modules.safe_class import SafeClass


class Controller(SafeClass):
    _required_input_cols = dict([("email", "email"), ("fam", "Фамилия"), ("name", "Имя"), ("otch", "Отчество"),
                                 ("town", "Город"), ("school", "Школа"), ("team", "Команда"),
                                 ("klass", "Класс")])
    _default_rename = _required_input_cols.copy()
    _default_rename.update([("aud", "Аудитория"), ("row", "Ряд"), ("col", "Место")])
    _default_output_cols = ["email", "fam", "name", "otch", "town", "school", "team", "klass", "aud", "row", "seat"]

    def __init__(self, filename, from_pickle=False):
        if from_pickle:
            data = pickle.load(open(filename, "rb"))
            Checker.clean_global_init(data["checker_meta"])
            Seat.counters = data["seats_meta"]
            self.__dict__.update(data["controller"].__dict__)
            return
        self.key_holder = set()
        self.last_change = None
        self.people = pd.DataFrame()
        self.auds = list()
        self.inds = list()
        self.teams = list()
        self.seed = 1
        found_main_settings = False
        excel_file = ExcelFile(filename)
        for name in excel_file.sheet_names:
            raw_frame = excel_file.parse(name, index_col=None, header=None)
            unresolved_dict = splitter(raw_frame, named=True)
            if "main_settings" in unresolved_dict.keys():
                if found_main_settings:
                    print("В {0} две страницы с общими настройками".format(filename))
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
                self.auds.append(Auditory(unresolved_dict, outer_name=name))
        all_names = [aud.inner_name for aud in self.auds]
        if len(all_names) < len(np.unique(all_names)):
            raise TypeError("В {0} есть одинаковые аудитории".format(filename))

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
        not_visited = set(self.auds)
        self._rand_loop_insert(data=data, available=not_visited)

    @mutable
    def rand_aud_team_insert(self, data):
        not_visited = set(self.auds)
        self._rand_loop_team_insert(data=data, available=not_visited)

    @mutable
    def _split_people(self):
        self.inds = self.people.query("team == 'и'").to_dict(orient="records")
        if not self.checker.settings["com_in_one"]:
            self.inds.extend(self.people.query("team != 'и'").to_dict(orient="records"))
        else:
            for team_number in list(np.unique(self.people.query("team != 'и'")["team"])):
                query = "team == " + str(team_number)
                self.teams.append(self.people.query(query).to_dict(orient="records"))

    @mutable
    def load_people(self, filename):
        self.inds = list()
        self.teams = list()
        people = pd.read_excel(filename, sheetname=0).applymap(clr)
        if not self._check_settings(fact=set(people.columns),
                                    req=set(self._required_input_cols.values()),
                                    way="=="):
            raise NotEnoughSettings(fact=set(people.columns),
                                    req=set(self._required_input_cols.values()),
                                    way="==")
        people = people.rename(columns=swap(self._required_input_cols))
        people["klass"] = people["klass"].apply(lambda x: get_numbers(x)[0])
        self.people = people
        self._split_people()

    @mutable
    def clean_all(self):
        for aud in self.auds:
            aud.clean_all()

    @mutable
    def lock_all(self, key):
        for aud in self.auds:
            aud.lock_all(key)
        self.key_holder.add(key)

    @mutable
    def unlock_all(self, key):
        if key in self.key_holder:
            for aud in self.auds:
                aud.unlock_all(key)
            self.key_holder.remove(key)
        else:
            raise KeyError(key)

    @mutable
    def erase_loaded_people(self):
        self.people = pd.DataFrame()
        self.inds = list()
        self.teams = list()

    @mutable
    def place_them(self):
        if len(self.people) and len(self.seated_people):
            if (set(self.people["email"])) & set(self.seated_people["email"]):
                message = "{} загруженных участников рассажены!"
                message = message.format(len(set(self.people["email"]) & set(self.seated_people["email"])))
                raise ControllerException(message)
        max_iter_number = 20
        random.seed(self.seed)
        try:
            for team in self.teams:
                self.rand_aud_team_insert(team)
            for individual in self.inds:
                self.rand_aud_insert(individual)
        except NoFreeAuditory:
            self.clean_all()
            if self.seed <= max_iter_number:
                self.seed += 1
                self.place_them()
            else:
                raise NoFreeAuditory("{0} итераций были безуспешны, слишком мало аудиторий".format(max_iter_number))

    @property
    def seated_people(self):
        seated = list()
        for aud in sorted(self.auds):
                seated.extend(aud.get_all_seated())
        frame = pd.DataFrame.from_dict(seated)
        return frame

    def whole_summary(self):
        message = ""
        for aud in sorted(self.auds):
            message += aud.summary() + "\n"
        return message

    def xlsx_summary(self):
        filename = "Сводка по аудиториям.xlsx"
        summary = list()
        for aud in self.auds:
            summary.append(aud.info())
        table = pd.DataFrame.from_records(summary, index="name")
        table.ix[:, Auditory.info_order].to_excel(filename)

    def dump_seated(self):
        filename = "Рассаженные участники.xlsx"
        select = ["fam", "name", "otch", "aud", "row", "col"]
        frame = self.seated_people
        frame.ix[:, select].sort_values("fam", ascending=True).rename(columns=self._default_rename).to_excel(filename, index=False)

    def write_maps_with_data(self, wbname, data):
        workbook = xlsxwriter.Workbook(wbname)
        form = workbook.add_format()
        form.set_font_size(30)
        form.set_bold()
        for aud in self.auds:
            sheet = workbook.add_worksheet(aud.inner_name)
            aud.map_with_data_to_writer(sheet, form, data)
        workbook.close()

    def write_maps_with_status(self, wbname):
        workbook = xlsxwriter.Workbook(wbname)
        form = workbook.add_format()
        form.set_font_size(30)
        form.set_bold()
        for aud in self.auds:
            sheet = workbook.add_worksheet(aud.inner_name)
            aud.map_with_status_to_writer(sheet, form)
        workbook.close()

    def to_pickle(self, path):
        prepared = dict([("checker_meta", Checker.settings),
                         ("seats_meta", Seat.counters),
                         ("controller", self)])
        with open(path, "wb") as f:
            pickle.dump(prepared, f)

    @property
    def info(self):
        info = dict()
        info["last_change"] = self.last_change
        info["n_auds"] = len(self.auds)
        info["n_used_auds"] = sum([aud.settings["available"] for aud in self.auds])
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
Всего мест {seats_total: <4}, посажено {seated}
        """.format(**self.info)
        return message
