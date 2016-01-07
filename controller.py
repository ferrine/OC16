from auditory import Auditory
from check_system import Checker
from rassadka_exceptions import *
from pandas import ExcelFile
from excelprocessor.reader import splitter
import numpy as np
import random
import pandas as pd
import xlsxwriter


def clr(x):
    try:
        return x.strip()
    except AttributeError:
        return x


def get_numbers(string):
    if isinstance(string, int):
        return list([string])
    elif isinstance(string, str):
        return [int(s) for s in string.split() if s.isdigit()]


class Controller:
    _default_input_cols = ["email", "fam", "name", "otch", "town", "school", "team", "klass"]
    _default_output_cols = ["email", "fam", "name", "otch", "town", "school", "team", "klass", "aud", "row", "seat"]
    _default_rename = dict([("fam", "Фамилия"), ("name", "Имя"), ("otch", "Отчество"),
                            ("aud", "Аудитория"), ("row", "Ряд"), ("col", "Место"),
                            ("town", "Город"), ("school", "Школа"), ("team", "Команда"),
                            ("klass", "Класс")])
    people = None
    inds = list()
    teams = list()
    seed = 1

    def __init__(self, filename):
        self.auds = list()
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
                Checker.global_init(unresolved_dict)
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

    def rand_aud_insert(self, data):
        not_visited = set(self.auds)
        self._rand_loop_insert(data=data, available=not_visited)

    def rand_aud_team_insert(self, data):
        not_visited = set(self.auds)
        self._rand_loop_team_insert(data=data, available=not_visited)

    def split_people(self):
        self.inds = self.people.query("team == 'и'").to_dict(orient="records")
        if not self.checker.settings["com_in_one"]:
            self.inds.extend(self.people.query("team != 'и'").to_dict(orient="records"))
        else:
            for team_number in list(np.unique(self.people.query("team != 'и'")["team"])):
                query = "team == " + str(team_number)
                self.teams.append(self.people.query(query).to_dict(orient="records"))

    def load_people(self, filename):
        people = pd.read_excel(filename, sheetname=0).applymap(clr)
        # было бы неплохо тут все проверить на правильность ввода
        people.columns = self._default_input_cols
        people["klass"] = people["klass"].apply(lambda x: get_numbers(x)[0])
        self.people = people

    def place_them(self):
        max_iter_number = 20
        random.seed(self.seed)
        try:
            for team in self.teams:
                self.rand_aud_team_insert(team)
            for individual in self.inds:
                self.rand_aud_insert(individual)
        except NoFreeAuditory:
            for aud in self.auds:
                aud.clean_all()
            if self.seed <= max_iter_number:
                self.seed += 1
                self.place_them()
            else:
                raise NoFreeAuditory("{0} итераций были безуспешны, слишком мало аудиторий".format(max_iter_number))

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
        seated = list()
        for aud in sorted(self.auds):
                seated.extend(aud.get_all_seated())
        frame = pd.DataFrame.from_dict(seated)
        select = ["fam", "name", "otch", "aud", "row", "col"]
        frame.ix[:, select].sort_values("fam", ascending=True).rename(columns=self._default_rename).to_excel(filename)

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
