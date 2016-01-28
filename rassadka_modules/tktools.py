import tkinter as tk
from collections import OrderedDict as oDict


class TkTools:
    # Abstract class

    @staticmethod
    def _create_menu(parent, dictionary, cascadeopts=None,
                     menuopts=None, itemopts=None, menubindage=None):
        """
        loop initial
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
                parent.add_command(label=key, **item, **itemopts)
            elif type(item) is oDict:
                child = tk.Menu(parent, **menuopts)
                TkTools._create_menu(child, item, cascadeopts, menuopts, itemopts, menubindage)
                parent.add_cascade(label=key, menu=child, **cascadeopts)
                for event, func in menubindage.items():
                    parent.bind(event, func)
            else:
                raise TypeError("dict or oDict expected")



