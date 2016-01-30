import os
import tkinter as tk
from tkinter import filedialog
from rassadka_modules.check_system import Checker
from rassadka_modules.auditory import Auditory
from collections import OrderedDict as oDict
from rassadka_modules.controller import Controller
from rassadka_modules.tktools import TkTools
from tkinter.messagebox import showerror


class Settings(tk.Toplevel):

    def __init__(self, master, items, *args, **kwargs):
        tk.Toplevel.__init__(self, master=master, *args, **kwargs)
        self.geometry("+500+300")
        self.items = {item.inner_name: item for item in items}
        self.buttons_lay = dict()
        self.current = tk.StringVar(self, "None")
        self.select_menu = tk.OptionMenu(self, self.current, *[item.inner_name for item in items],
                                         command=self._make_layout)
        self.select_menu.grid(row=0, column=0, columnspan=2, sticky="we")

    def _make_layout(self, name):
        for widget in self.buttons_lay.values():
            widget.grid_forget()
        item = self.items[name]
        self.buttons_lay = dict()
        self.vars = dict()
        self.row = 1
        self._check_buttons(self.row, item)
        self._radio_buttons(self.row, item)
        self._scale_buttons(self.row, item)
        self._make_button(self.row, item)

    def _make_button(self, start_row, item):
        def _commit_action():
            new_settings = {setting: var.get() for setting, var in self.vars.items()}
            item.refresh(new_settings)
            self.buttons_lay["__label__"] = tk.Label(self, text="OK",
                                                     justify="left",
                                                     font="Courier 7")
            self.buttons_lay["__label__"].grid(column=3, row=start_row)
        self.buttons_lay["__commit__"] = tk.Button(self, text="Закончить настройку", command=_commit_action)
        self.buttons_lay["__commit__"].grid(column=1, row=start_row, columnspan=2, sticky="we")

    def _check_buttons(self, start_row, item):
        if "CHECK" not in dir(item):
            return
        pos = 0
        row = 0
        for setting in item.CHECK:
            self.vars[setting] = tk.BooleanVar(self, value=item.settings[setting])
            self.buttons_lay[setting] = tk.Checkbutton(master=self, text=setting, variable=self.vars[setting])
            self.buttons_lay[setting].grid(row=pos // 4 + start_row, column=pos % 4,
                                           sticky="w")
            pos += 1
            row = pos // 4 + (pos % 4)
        self.row = start_row + row

    def _radio_buttons(self, start_row, item):
        if "RADIO" not in dir(item):
            return
        row = 0
        for setting in item.RADIO:
            pos = 0
            self.vars[setting["name"]] = tk.IntVar(self, value=item.settings[setting["name"]])
            for state in setting["states"]:
                self.buttons_lay[setting["name"]] = tk.Radiobutton(self, text=setting["name"] + " = " + str(state),
                                                                   value=state,
                                                                   variable=self.vars[setting["name"]])
                self.buttons_lay[setting["name"]].grid(row=row + start_row, column=pos % 4,
                                                       sticky="w")
                pos += 1
            row = pos // 4 + (pos % 4)
        self.row = start_row + row + 1

    def _scale_buttons(self, start_row, item):
        if "SCALE" not in dir(item):
            return
        row = 0
        for setting in item.SCALE:
            self.vars[setting["name"]] = tk.DoubleVar(self, value=item.settings[setting["name"]])
            self.buttons_lay[setting["name"]] = tk.Scale(self, label=setting["name"],
                                                         variable=self.vars[setting["name"]],
                                                         from_=setting["var"][0],
                                                         to=setting["var"][1],
                                                         orient="horizontal",
                                                         resolution=0.01)
            self.buttons_lay[setting["name"]].grid(row=row + start_row, column=0, sticky="w")
            row += 1
        self.row = start_row + row


class RassadkaGUI(tk.Tk, TkTools):
    __SIZE = (500, 250, 500, 250)
    __GUI_GEOM = "%dx%d+%d+%d" % __SIZE
    __POP_POS = "+" + str(int(__SIZE[2] + 0.5 * __SIZE[0])) + "+" + str(int(__SIZE[3] + 0.5 * __SIZE[1]))
    __CONTROLLER_FILENAME = "controller.pkl"
    __DEFAULT_APP_PATH = os.environ.get("USERPROFILE") + "\\.rassadka\\"
    if not os.path.exists(__DEFAULT_APP_PATH):
        os.mkdir(__DEFAULT_APP_PATH)

    def _load_controller(self):
        try:
            file = open(self.__DEFAULT_APP_PATH + self.__CONTROLLER_FILENAME, "rb")
            self.controller = Controller(file, from_pickle=True)
        except FileNotFoundError:
            filename = filedialog.Open(self,
                                       filetypes=[("Excel file", ".xlsx")]).show()
            if not filename:
                self.destroy()
            file = open(filename, "rb")
            self.controller = Controller(file)
        self.infovar.set(str(self.controller))

    def task(self, ev):
            self.infovar.set(str(self.controller))
            self.update_idletasks()

    def upd(self, event=tk.Event):
        self.after(200, self.task, event)

    def __init__(self):
        tk.Tk.__init__(self)
        self.__SAVE_ON_EXIT = tk.BooleanVar(self, value=True)
        self.geometry(self.__GUI_GEOM)
        self.label = tk.Label(self, text="Tap anywhere to refresh info",
                              justify="left",
                              font="Courier 7")
        self.label.grid(row=1, column=0, sticky="w")
        self.pack_propagate(1)
        self.infovar = tk.StringVar(self)
        self._load_controller()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.info = tk.Label(self, textvariable=self.infovar,
                             justify="left",
                             font="Courier 10")
        self.info.grid(row=0, column=0)
        menu = tk.Menu(self)
        commands = oDict()
        commands["Загрузки"] = oDict()
        commands["Выгрузки"] = oDict()
        commands["Волшебство"] = oDict()
        commands["Загрузки"]["Загрузить участников"] = {"command":
                                                        self.load(parent=self, item=self.controller.load_people)}
        commands["Загрузки"]["Загрузить Emails"] = {"command":
                                                    self.load(parent=self, item=self.controller.load_emails)}
        commands["Загрузки"]["Очистить загруженных"] = {"command": self.controller.clear_buffer}
        commands["Загрузки"]["Добавить аудиторию"] = {"command": self.load(self, self.controller.load_auditory)}
        commands["Выгрузки"]["На стенд"] = {"command": self.save(parent=self, item=self.controller.seated_to_excel,
                                            for_item=dict(full=False))}
        commands["Выгрузки"]["Полная выгрузка"] = {"command":
                                                   self.save(parent=self, item=self.controller.seated_to_excel,
                                                             for_item=dict(full=True))}
        commands["Выгрузки"]["Раздатка"] = {"command": self.save(parent=self, item=self.controller.razdatka_to_excel)}
        commands["Выгрузки"]["Карты..."] = oDict()
        commands["Выгрузки"]["Карты..."]["Карта с классами"] = {"command": self.save(self,
                                                                item=self.controller.maps_with_data_to_excel,
                                                                for_item=dict(data="klass"),
                                                                filetypes=(('Excel files', '.xlsx'), ))}
        commands["Выгрузки"]["Карты..."]["Карта с местами"] = {"command": self.save(self,
                                                               item=self.controller.maps_with_status_to_excel,
                                                               filetypes=(('Excel files', '.xlsx'), ))}
        commands["Выгрузки"]["Аудитории..."] = oDict()
        commands["Выгрузки"]["Аудитории..."]["..в txt"] = {"command": self.save(parent=self,
                                                           item=self.controller.summary_to_txt,
                                                           filetypes=(("txt files", ".txt"), ))}
        commands["Выгрузки"]["Аудитории..."]["..в Excel"] = {"command": self.save(parent=self,
                                                             item=self.controller.summary_to_excel,
                                                             filetypes=(("Excel files", ".xlsx"), ))}
        commands["Волшебство"]["Рассадить"] = {"command": self.controller.place_loaded_people}
        commands["Волшебство"]["Закрепить на ключ"] = {"command": self.key_usage(func=
                                                                                 self.controller.lock_seated_on_key)}
        commands["Волшебство"]["Открепить по ключу"] = {"command": self.key_usage(func=
                                                                                  self.controller.unlock_seated_by_key)}
        commands["Волшебство"]["Отметка о прибытии"] = {"command": self.controller.mark_arrival_by_email}
        commands["Волшебство"]["Удалить..."] = oDict()
        commands["Волшебство"]["Удалить..."]["..по местам"] = {"command": self.controller.remove_seated_by_coords}
        commands["Волшебство"]["Удалить..."]["..по Email"] = {"command": self.controller.remove_seated_by_email}
        commands["Волшебство"]["Опасно"] = oDict()
        commands["Волшебство"]["Опасно"]["Удалить всех"] = {"command": self.controller.clean_seated}
        commands["Волшебство"]["Опасно"]["Обновить по местам"] = {"command":
                                            self.yes_no(lambda event: self.controller.update_seated_by_coords(True),
                                                        lambda event: self.controller.update_seated_by_coords(False),
                                                        label="Игнорировать ли блокировку?")}
        commands["Волшебство"]["Опасно"]["Очень опасно"] = oDict()    
        commands["Волшебство"]["Опасно"]["Очень опасно"]["Удалить загрузочный файл"] = { 
            "command": lambda: self.__SAVE_ON_EXIT.set(False),
            "background": "red"
        }
        commands["Волшебство"]["Опасно"]["Очень опасно"]["Удалить аудиторию"] = {
            "command": self.key_usage(self.controller.delete_auditory, label="Название аудитории"),
            "background": "red"
        }
        self.test_button = tk.Button(text="Настройки",
                                     command=lambda: Settings(self, [Checker] +
                                                              sorted(list(self.controller.auds.values()))))
        self.test_button.grid(column=0, columnspan=2, sticky="we")
        self._create_menu(menu, commands, menuopts=dict(tearoff=0))
        self.bind_all("<Button-1>", self.upd, add="+")
        self.config(menu=menu)

    def load(self, parent, item, for_item=None, **kwargs):
        if not for_item:
            for_item = dict()

        def wrapper():
            dialog = filedialog.Open(parent, filetypes=(('Excel files', '.xlsx'),), **kwargs)
            filename = dialog.show()
            if not filename:
                return
            file = open(filename, "rb")
            item(file=file, **for_item)
            self.upd()
        return wrapper

    def save(self, parent, item, filetypes=(('Excel files', '.xlsx'),), for_item=None, **kwargs):
        if not for_item:
            for_item = dict()

        def wrapper():
            path = tk.filedialog.SaveAs(parent, filetypes=filetypes,
                                        initialfile="output", **kwargs).show()
            if not path:
                return
            if not path.endswith(filetypes[0][-1]):
                path = path + filetypes[0][-1]
            file = open(path, "w" if path.endswith(".txt") else "wb")
            item(file=file, **for_item)
            self.upd()
        return wrapper

    def on_exit(self):
        if self.__SAVE_ON_EXIT.get():
            self.controller.to_pickle(open(self.__DEFAULT_APP_PATH + self.__CONTROLLER_FILENAME, "wb"))
        else:
            try:
                os.remove(self.__DEFAULT_APP_PATH + self.__CONTROLLER_FILENAME)
            except (NotImplementedError, FileNotFoundError):
                pass
        self.destroy()

    def key_usage(self, func, label="Key"):
        def wrapper():
            pop_up = tk.Toplevel(self)
            pop_up.geometry(self.__POP_POS)
            tk.Label(pop_up, text=label).grid(column=0, row=0, sticky="e")
            inp = tk.Entry(pop_up, width=16)
            inp.grid(column=1, row=0)

            def ok(event):
                user_input = inp.get()
                func(user_input)

            button = tk.Button(pop_up, text="OK", command=pop_up.destroy)
            button.bind("<Button-1>", ok, add="+")
            button.bind("<Button-1>", self.upd, add="+")
            button.grid(column=0, row=1, columnspan=2, sticky="we")
        return wrapper

    def yes_no(self, yes_event, no_event, label=""):
        def wrapper():
            pop_up = tk.Toplevel(self)
            pop_up.geometry(self.__POP_POS)
            pop_up.label = tk.Label(pop_up, text=label)
            pop_up.label.pack(side="top")
            yes = tk.Button(pop_up, text="Да", command=pop_up.destroy)
            no = tk.Button(pop_up, text="Нет", command=pop_up.destroy)
            no.bind("<Button-1>", no_event, add="+")
            yes.bind("<Button-1>", yes_event, add="+")
            no.bind("<Button-1>", self.upd, add="+")
            yes.bind("<Button-1>", self.upd, add="+")
            yes.pack(side="left")
            no.pack(side="right")
        return wrapper

    #def report_callback_exception(self, exc, val, tb):
    #    showerror("Ошибка", message=str(val))


if __name__ == '__main__':
    gui = RassadkaGUI()
    gui.mainloop()