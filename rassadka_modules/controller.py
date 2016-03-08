import pickle
import random
import numpy as np
import pandas as pd
import xlsxwriter
import warnings

from functools import reduce
from pandas import ExcelFile
from collections import OrderedDict as oDict
from rassadka_modules.auditory import Auditory, Seat
from rassadka_modules.check_system import Checker
from rassadka_modules.common import clr, swap, mutable
from rassadka_modules.excelprocessor.reader import splitter
from rassadka_modules.rassadka_exceptions import *
from rassadka_modules.safe_class import SafeClass


class Controller(SafeClass):
    required_data_cols = oDict([("email", "email"), ("fam", "Фамилия"), ("name", "Имя"), ("otch", "Отчество"),
                                ("town", "Город"), ("school", "Школа"), ("team", "Команда"),
                                ("klass", "Класс")])
    _default_full_dict = required_data_cols.copy()
    _default_full_dict.update([("aud", "Ауд."), ("row", "Ряд"),
                               ("col", "Место"), ("arrived", "Отметка о прибытии"), ("key", "Ключ")])
    _mini_out = ["fam", "name", "otch", "aud", "row", "col"]
    _razdatka_cols = ["fam", "name", "otch", "row", "col", "Пришел?"]
    max_iter = 20

    def __getitem__(self, item):
        return self.auds[item]

    def __init__(self, file, from_pickle=False):
        if from_pickle:
            data = pickle.load(file)
            Checker.clean_global_init(data["checker_meta"])
            Seat.counters = data["seats_meta"]
            self.__dict__.update(data["controller"].__dict__)
            return
        self.email_handle = list()
        self.mode = {"people": "None"}
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
                    raise ControllerException("Две страницы с общими настройками!")
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
                    del tmp
                    raise TypeError("Есть одинаковые аудитории")
                else:
                    self.auds[tmp.inner_name] = tmp
        self._message_upd()

    def coords_by_email(self, email) -> dict:
        """
        Ищет место, на котором сидит участник с указанным email
        :param email:
        :return:
        """
        for aud in self.auds.values():
            try:
                result = aud.coords_by_email_in_aud(email)
                return result
            except KeyError:
                continue
        raise KeyError(email)

    def _rand_loop_insert(self, data, available):
        """
        Рекурсивная часть
        :param dict data: чел
        :param set available: оставшиеся аудитрии на проверку
        :return:
        """
        if not available:
            raise NoFreeAuditory("Нет свободных аудиторий")
        for_check = random.sample(available, 1)[0]
        available.remove(for_check)
        try:
            for_check.rand_insert(data)
        except EndLoopException:
            self._rand_loop_insert(data, available)

    def _rand_loop_team_insert(self, data, available):
        """
        Рекурсивная часть
        :param dict data:
        :param set available:
        :return:
        """
        if not available:
            raise NoFreeAuditory("Нет свободных аудиторий")
        for_check = random.sample(available, 1)[0]
        available.remove(for_check)
        try:
            for_check.rand_insert_team(data)
        except EndLoopException:
            self._rand_loop_team_insert(data, available)

    def _split_people(self):
        """
        Блок разбивает загруженных людей
        в пачки команд и индивидуалов в
        соответствии с настройками
        """
        tmp = pd.DataFrame(self.people.drop(["aud", "row", "col"], errors="ignore", axis=1))
        self.inds = tmp.query("team == 'и'").to_dict(orient="records")
        if not self.checker.settings["com_in_one"]:
            self.inds.extend(tmp.query("team != 'и'").to_dict(orient="records"))
        else:
            for team_number in list(np.unique(tmp.query("team != 'и'")["team"])):
                query = "team == " + str(team_number)
                self.teams.append(tmp.query(query).to_dict(orient="records"))

    @mutable
    def switch_on_aud(self, audname):
        self.auds[audname].switch_on()

    @mutable
    def switch_off_aud(self, audname):
        self.auds[audname].switch_off()

    @mutable
    def load_auditory(self, file):
        """
        Повторяющиеся загружены не будут
        :param file:
        :return:
        """
        excel_file = ExcelFile(file)
        for name in excel_file.sheet_names:
            raw_frame = excel_file.parse(name, index_col=None, header=None)
            unresolved_dict = splitter(raw_frame, named=True)
            if "settings" in unresolved_dict.keys():
                tmp = Auditory(unresolved_dict, outer_name=name)
                if tmp.inner_name in self.auds.keys():
                    del tmp
                else:
                    self.auds[tmp.inner_name] = tmp

    @mutable
    def delete_auditory(self, audname):
        try:
            del self.auds[str(audname)]
        except KeyError:
            raise ControllerException("Такой аудитории не существует: {}".format(audname))

    @mutable
    def load_emails(self, file):
        table = pd.read_excel(file, sheetname=0).applymap(clr)
        if not self._check_settings(fact=set(table.columns),
                                    req={"email"},
                                    way=">="):
            raise NotEnoughSettings(fact=set(table.columns),
                                    req={"email"},
                                    way=">=")
        self.email_handle = list(table.to_dict()["email"].values())

    @mutable
    def load_people(self, file):
        """
        Требования к входным данным:
        1) см required_data_cols
        2) если с целью получить права editor, то
           надо дополнительно указать все места
           Аудитория, Ряд, Место
        """
        self.inds = list()
        self.teams = list()
        people = pd.read_excel(file, sheetname=0).applymap(clr)
        if not self._check_settings(fact=set(people.columns),
                                    req=set(self.required_data_cols.values()),
                                    way=">="):
            raise NotEnoughSettings(fact=set(people.columns),
                                    req=set(self.required_data_cols.values()),
                                    way=">=")
        people = people.rename(columns=swap(self._default_full_dict))
        if (any([item in people.columns for item in ["aud", "row", "col"]]) and
                not all([item in people.columns for item in ["aud", "row", "col"]])):
            raise ControllerException("Некорректно заданы столбцы с местами")
        # Присвоение уровня доступа
        if len(people) == 0:
            self.mode["people"] = "None"            # Нельзя ничего делать с рассаженными участниками
            return
        elif "aud" in people.columns:
            self.mode["people"] = "input/edit"      # Можно менять информацию, изымать и добавлять
        else:
            self.mode["people"] = "input"           # Можно только добавлять
        self.people = people
        self._split_people()

    def rand_aud_insert_team(self, data):
        not_visited = set(self.auds.values())
        self._rand_loop_team_insert(data=data, available=not_visited)

    def rand_aud_insert(self, data):
        not_visited = set(self.auds.values())
        self._rand_loop_insert(data=data, available=not_visited)

    @mutable
    def clean_seated(self):
        """
        Изымает абсолютно всех незаблокированных(!)
        участников из аудиторий
        :return:
        """
        for aud in self.auds.values():
            aud.clean_all()

    @mutable
    def lock_seated_on_key_by_email(self, key: str):
        """
        Блокироует участников по ключу.
        Это позволяет получать определенного
        рода спокойствие за исполняемые опасные
        действия над рассаженными участниками
        :param key: Ключ
        :return:
        """
        if not key:
            raise ControllerException("Некорректный ключ")
        if not self.email_handle:
            raise ControllerException("Список email-ов пуст")
        for email in self.email_handle:
            coords = self.coords_by_email(email)
            self.auds[coords["aud"]].lock_by_coords((coords["row"], coords["col"]), key)

    @mutable
    def unlock_seated_by_email(self):
        """
        Разблокировывает участников по email игнорирует ключи
        """
        if not self.email_handle:
            raise ControllerException("Список email-ов пуст")
        for email in self.email_handle:
            coords = self.coords_by_email(email)
            self.auds[coords["aud"]].unlock_by_coords((coords["row"], coords["col"]))

    @mutable
    def lock_seated_on_key(self, key: str):
        """
        Блокироует участников по ключу.
        Это позволяет получать определенного
        рода спокойствие за исполняемые опасные
        действия над рассаженными участниками
        :param key: Ключ
        :return:
        """
        if not key:
            raise ControllerException(key)
        for aud in self.auds.values():
            aud.lock_all(key)

    @mutable
    def unlock_seated_by_key(self, key):
        """
        Разблокировывает участников по ключу
        :param str key: Ключ
        :return:
        """
        if key in self.key_holder:
            for aud in self.auds.values():
                aud.unlock_all(key)
        else:
            raise ControllerException("Key Error %s" % key)

    @mutable
    def mark_arrival_by_email(self):
        """
        Ставит отметку о прибытии для участников, чьи email подгружены
        """
        if not self.email_handle:
            raise ControllerException("Список email-ов пуст")
        for email in self.email_handle:
            try:
                seat = self.coords_by_email(email)
                self.auds[str(seat["aud"])].mark_arrival_by_coords((seat["row"], seat["col"]))
            except KeyError:
                continue

    @mutable
    def update_seated_by_coords(self, forced=False):
        """
        Меняет всю информацию на актуальную.
        Необходимо иметь места, где менять и
        загруженных людей(что менять)
        :param bool forced: менять ли людей на местах, которые заблокированы?
        """
        if "edit" not in self.mode["people"].split("/"):     # Проверка уровня доступа
            raise ControllerException("PermissionError")
        for new_data in self.people.to_dict(orient="records"):
            for_insert = new_data.copy()
            del for_insert["aud"], for_insert["row"], for_insert["col"]
            self.auds[new_data["aud"]].update_by_coords((new_data["row"], new_data["col"]), for_insert, forced=forced)

    @mutable
    def update_seated_by_email(self, forced=False):
        """
        Меняет всю информацию на актуальную.
        Необходимо иметь обычную допустимую входную загрузку
        :param bool forced: менять ли людей на местах, которые заблокированы?
        """
        if "input" not in self.mode["people"].split("/"):     # Проверка уровня доступа
            raise ControllerException("PermissionError")
        for new_data in self.people.to_dict(orient="records"):
            for_insert = new_data.copy()
            coords = self.coords_by_email(for_insert["email"])
            if "edit" in self.mode["people"].split("/"):
                del for_insert["aud"], for_insert["row"], for_insert["col"]
            self.auds[coords["aud"]].update_by_coords((coords["row"], coords["col"]), for_insert, forced=forced)

    @mutable
    def remove_seated_by_coords(self):
        """
        Изымает всех людей по указанным местам.
        Необходимо иметь места.
        Не изымает людей с заблокированных мест.
        """
        if "edit" not in self.mode["people"].split("/"):     # Проверка уровня доступа
            raise ControllerException("PermissionError")
        for remove_data in self.people.to_dict(orient="records"):
            self.auds[remove_data["aud"]].remove_by_coords((remove_data["row"], remove_data["col"]))

    @mutable
    def remove_seated_by_email(self):
        """
        Изымает всех людей по указанным email.
        Необходимо иметь подгруженные email.
        Не изымает с заблокированных мест.
        """
        if not bool(self.email_handle):
            raise ControllerException("Список email-ов пуст")
        for email in self.email_handle:
            try:
                seat = self.coords_by_email(email)
                self.auds[seat["aud"]].remove_by_coords((seat["row"], seat["col"]))
            except KeyError:
                continue

    @mutable
    def clear_buffer(self):
        """
        Очистить подгруженных людей и emails.
        Обнуляет уровень доступа.
        """
        self.people = pd.DataFrame()
        self.inds = list()
        self.teams = list()
        self.email_handle = list()
        self.mode["people"] = "None"

    @mutable
    def place_loaded_people(self):
        """
        Рассаживает подгруженных участников
        """
        if "input" not in self.mode["people"].split("/"):
            raise ControllerException("PermissionError")
        if len(self.people) and len(self.seated_people):
            if (set(self.people["email"])) & set(self.seated_people["email"]):
                message = "{} загруженных участников рассажены!"
                message = message.format(len(set(self.people["email"]) & set(self.seated_people["email"])))
                raise ControllerException(message)
        random.seed(self.seed)
        for team in self.teams:
            self.rand_aud_insert_team(team)
        for individual in self.inds:
            self.rand_aud_insert(individual)

    @property
    def seated_people(self) -> pd.DataFrame:
        """
        Собирает в общую табличку всех рассаженных участников
        """
        seated = list()
        for aud in sorted(self.auds.values()):
            seated.extend(aud.get_all_seated())
        frame = pd.DataFrame.from_dict(seated)
        return frame

    def comparison(self):
        if len(self.people) and len(self.seated_people):
            other = self.people.set_index("email", drop=False)
            seated = self.seated_people.set_index("email", drop=False)
            emails = set(seated.index.tolist()) & set(other.index.tolist())
            not_seated = set(other.index.tolist()) - set(seated.index.tolist())
            result = {"there": list(), "here": list()}
            for email in emails:
                here = seated.loc[email].to_dict()
                there = other.loc[email].to_dict()
                for key in self.required_data_cols.keys():
                    if clr(here[key]) != clr(there[key]):
                        result["there"].append(there)
                        result["here"].append(here)
                        break
            result["not_seated"] = other.loc[not_seated].rename(columns=self._default_full_dict)
        else:
            result = {"there": list(), "here": list(), "not_seated": pd.DataFrame()}
        if len(self.email_handle) and len(self.seated_people):
            seated = self.seated_people.set_index("email", drop=False)
            result["emails_not_seated"] = pd.DataFrame(list(set(self.email_handle) - set(seated.index.tolist())))
        else:
            result["emails_not_seated"] = pd.DataFrame()
        return {"here": pd.DataFrame.from_records(result["here"]).rename(columns=self._default_full_dict),
                "there": pd.DataFrame.from_records(result["there"]).rename(columns=self._default_full_dict),
                "not_seated": result["not_seated"],
                "emails_not_seated": result["emails_not_seated"]}

    @property
    def not_seated(self):
        if not len(self.people) or not len(self.seated_people):
            raise ControllerException("Нету людей для сравнения")
        other = self.people.set_index("email", drop=False)
        seated = self.seated_people.set_index("email", drop=False)
        emails = set(other.index.tolist()) - set(seated.index.tolist())
        return other.loc[emails]

    def summary_to_txt(self, file):
        message = ""
        for aud in sorted(self.auds.values()):
            message += aud.summary + "\n"
        file.write(message)

    def summary_to_excel(self, file):
        with pd.ExcelWriter(file) as writer:
            summary = list()
            for aud in sorted(self.auds.values()):
                summary.append(aud.info)
            table = pd.DataFrame.from_records(summary, index="name")
            table.ix[:, Auditory.export_names.keys()].rename(columns=Auditory.export_names).to_excel(writer)

    def seated_to_excel(self, file, full=False):
        """
        Выводит в эксель инфу по участникам, с их местами и тд
        :param file: куда выводить
        :param bool full: всю ли инфу выводить или только на стенд?
        :return:
        """
        with pd.ExcelWriter(file) as writer:
            if not full:
                select = self._mini_out
            else:
                select = list(self._default_full_dict.keys())
            frame = self.seated_people
            frame.ix[:, select].sort_values("fam", ascending=True).rename(
                columns=self._default_full_dict).reset_index(drop=True).to_excel(writer, "На стенд")
            sheet = writer.sheets["На стенд"]
            sheet.set_column("B:D", 15)
            sheet.repeat_rows(0)
            sheet.hide_gridlines(0)
            sheet.set_paper(9)

    def maps_with_data_to_excel(self, data, file):
        """
        Выводит карту рассадки в эксель с необходимой информацией
        :param file: куда выводим
        :param data: какая информация нужна
        """
        with xlsxwriter.Workbook(file) as workbook:
            form = workbook.add_format()
            form.set_align('center')
            form.set_bold()
            for aud in sorted(self.auds.values()):
                sheet = workbook.add_worksheet(aud.inner_name)
                aud.map_with_data_to_writer(sheet, form, data)
                sheet.set_header("&L&30 " + aud.inner_name)
                sheet.set_column(0, aud.shape[1], 6.5)
                sheet.hide_gridlines(0)
                if aud.inner_name.startswith("П"):
                    sheet.set_paper(8)
                    sheet.set_print_scale(75)
                else:
                    sheet.set_paper(9)
                sheet.set_landscape()
                sheet.fit_to_pages(1, 1)
                sheet.set_page_view()

    def maps_with_status_to_excel(self, file):
        """
        Выводит карту рассадка с пропечатанными местами в эксель
        :param file: куда выводим
        """
        with xlsxwriter.Workbook(file) as workbook:
            form = workbook.add_format()
            form.set_align('center')
            form.set_bold()
            for aud in sorted(self.auds.values()):
                sheet = workbook.add_worksheet(aud.inner_name)
                aud.map_with_status_to_writer(sheet, form)
                sheet.set_header("&L&30 " + aud.inner_name)
                sheet.hide_gridlines(0)
                sheet.set_column(0, aud.shape[1], 6.5)
                if aud.inner_name.startswith("П"):
                    sheet.set_paper(8)
                    sheet.set_print_scale(75)
                else:
                    sheet.set_paper(9)
                sheet.set_landscape()
                sheet.fit_to_pages(1, 1)
                sheet.set_page_view()

    def razdatka_to_excel(self, file):
        """
        Выводит списки с участниками в каждой аудитории в ексель
        :param file: куда выводим
        :return:
        """
        with pd.ExcelWriter(file) as writer:
            for aud in sorted(self.auds.values()):
                aud.people_table.ix[:, self._razdatka_cols].sort_values("fam", ascending=True).rename(
                    columns=self._default_full_dict).to_excel(
                    writer, aud.inner_name, index=False)
                sheet = writer.sheets[aud.inner_name]
                sheet.set_column("A:C", 15)
                sheet.repeat_rows(0)
                sheet.hide_gridlines(0)
                sheet.set_paper(9)
                sheet.set_header("&L&30 " + aud.inner_name)
                sheet.set_page_view()

    def to_pickle(self, file):
        """
        Сохраняемся вместе с классовой инфой
        :param file: куда сохраняемся
        """
        prepared = dict([("checker_meta", Checker.settings),
                         ("seats_meta", Seat.counters),
                         ("controller", self)])
        pickle.dump(prepared, file)

    @property
    def key_holder(self):
        return np.unique(reduce(list.__add__, [aud.keys for aud in self.auds.values()], []))

    @property
    def info(self):
        def s(x, subset, condition=None):
            if not len(x):
                return set()
            else:
                if not condition:
                    return set(x.ix[:, subset])
                else:
                    return set(x.query(condition).ix[:, subset])

        info = dict()
        info["last_change"] = self.last_change
        info["n_auds"] = len(self.auds)
        info["n_used_auds"] = sum([aud.settings["available"] for aud in self.auds.values()])
        info["seated_teams"] = len(reduce(lambda x, y: x.union(y), [aud.teams_set for aud in self.auds.values()]))
        info["arrived_teams"] = len(reduce(lambda x, y: x.union(y),
                                           [aud.teams_arrived_set for aud in self.auds.values()]))
        info["seats_available"] = sum([aud.capacity for aud in self.auds.values() if aud.settings["available"]])
        info["seated"] = Seat.total_seated()
        info["seats_total"] = sum([aud.capacity for aud in self.auds.values()])
        info["arrived"] = Seat.total_arrived()
        info["mode"] = self.mode["people"]
        info["emails"] = len(self.email_handle)
        info["people"] = len(self.people)
        info["intersect_teams"] = len(s(self.people, "team", condition="team != 'и'") & s(self.seated_people, "team"))
        info["intersect_people"] = len(s(self.people, "email") & s(self.seated_people, "email"))
        info["intersect_emails"] = len(set(self.email_handle) & s(self.seated_people, "email"))
        info["n_teams"] = len(self.teams)
        all_keys = reduce(list.__add__, [aud.keys for aud in self.auds.values()], [])
        key, frequency = np.unique(all_keys, return_counts=True)
        info["keys"] = dict(zip(key, frequency))
        return info

    def __str__(self):
        return self._message

    def update(self):
        self.last_change = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
        self._message_upd()

    def _message_upd(self):
        self._message = """
Последнее изменение {last_change}
Режим -{mode}-
Загружено(сидит) человек    {people:<5}({intersect_people})
                 команд     {n_teams:<5}({intersect_teams})
                 emails     {emails:<5}({intersect_emails})
Доступно(всего)  аудиторий  {n_used_auds:<5}({n_auds})
                 мест       {seats_available:<5}({seats_total})
Посажено(пришло) человек    {seated:<5}({arrived})
                 команд     {seated_teams:<5}({arrived_teams})
Ключи {{ключ: количество}}
    {keys}""".format(**self.info)




























