import tkinter as tk
from tkinter.messagebox import showerror
from collections import OrderedDict as oDict


class ExceptionRedirect:
        def __init__(self, func, exceptions=tuple()):
            self.func = func
            self.exceptions = exceptions

        def __call__(self, *args, **kwargs):
            if self.exceptions:
                try:
                    return self.func(*args, **kwargs)
                except self.exceptions as e:
                    showerror("Ошибка", message=str(e))
            else:
                return self.func(*args, **kwargs)


class TkTools:
    # Abstract class

    @staticmethod
    def _create_menu(parent, dictionary, redirect=tuple(), cascadeopts=None,
                     menuopts=None, itemopts=None, menubindage=None):
        """
        loop initial
        :param redirect: кортеж исключений, которые надо выводить
        :param tk.Menu parent:
        :param oDict | dict dictionary:
        :return:
        """
        if not cascadeopts:
            cascadeopts = dict()
        if not menuopts:
            menuopts = dict()
        if not itemopts:
            itemopts = dict()
        if not menubindage:
            menubindage = dict()

        for key, item in dictionary.items():
            if type(item) is dict:
                if "command" in item.keys():
                    item["command"] = ExceptionRedirect(item.get("command"), redirect)
                parent.add_command(label=key, **item, **itemopts)
            elif type(item) is oDict:
                child = tk.Menu(parent, **menuopts)
                TkTools._create_menu(child, item, redirect, cascadeopts, menuopts, itemopts, menubindage)
                parent.add_cascade(label=key, menu=child, **cascadeopts)
                for event, func in menubindage.items():
                    parent.bind(event, func)
            else:
                raise TypeError("dict or oDict expected")



