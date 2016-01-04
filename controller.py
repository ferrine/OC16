from auditory import Auditory
from check_system import Checker
from rassadka_exceptions import *
from pandas import ExcelFile
from excelprocessor.reader import splitter
import numpy as np
import random
import pandas as pd


def clr(x):
    try:
        return x.strip()
    except AttributeError:
        return x


class Controller:
    people = None
    inds = list()
    teams = list()

    def __init__(self, filename):
        self.auds = list()
        found_main_settings = False
        try:
            excel_file = ExcelFile(filename)
        except FileNotFoundError:
            raise FileNotFoundError("Файл {0} не найден".format(filename))
        for name in excel_file.sheet_names:
            raw_frame = excel_file.parse(name, index_col=None, header=None)
            unresolved_dict = splitter(raw_frame, named=True)
            if "main_settings" in unresolved_dict.keys():
                if found_main_settings:
                    Controller.out("В {0} две страницы с общими настройками".format(filename))
                    continue
                found_main_settings = True
                Checker.global_init(unresolved_dict)
            else:
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

    def rand_aud_insert(self, data):
        not_visited = set(self.auds)
        self._rand_loop_insert(data=data, available=not_visited)

    def rand_aud_team_insert(self, data):
        not_visited = set(self.auds)
        self._rand_loop_team_insert(data=data, available=not_visited)

    def _split_people(self):
        self.inds = self.people.query("team == 'и'").to_dict(orient="records")
        if not Checker.settings["com_in_one"]:
            self.teams = self.people.query("team != 'и'").to_dict(orient="records")
        else:
            for team_number in list(np.unique(self.people.query("team != 'и'")["team"])):
                query = "team == " + str(team_number)
                self.teams.append(self.people.query(query).to_dict(orient="records"))

    def load_people(self, filename):
        try:
            people = pd.read_excel(filename, sheetname=0).applymap(clr)
        except FileNotFoundError:
            raise FileNotFoundError("Файл {0} не найден".format(filename))
        # было бы неплохо тут все проверить на правильность ввода
        people.columns = ["id", "fam", "name", "otch", "town", "school", "team", "klass"]
        people["klass"] = people["klass"].apply(lambda x: int(x.split()[0]))
        self.people = people
        self._split_people()

    def place_them(self):
        try:
            for team in self.teams:
                self.rand_aud_team_insert(team)
            for individual in self.inds:
                self.rand_aud_insert(individual)
        except NoFreeAuditory:
            # Можно добавить дополнительный проход изменив random.seed
            pass

    def whole_summary(self):
        for aud in sorted(self.auds):
            self.out(aud.summary())

    def dump_seated(self, filename):
        if not filename.endswith(".xlsx"):
            raise FileExistsError(filename + " must have .xlsx extension")
        seated = list()
        for aud in sorted(self.auds):
                seated.extend(aud.get_all_seated())
        frame = pd.DataFrame.from_dict(seated)
        frame.to_excel(filename)

    @classmethod
    def out(cls, text):
        print(text)
