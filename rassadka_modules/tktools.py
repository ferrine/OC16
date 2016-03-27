import tkinter as tk
from collections import OrderedDict as oDict


class TkTools:
    # Mixin class

    @staticmethod
    def _create_menu(parent, dictionary, cascadeopts=None,
                     menuopts=None, itemopts=None, menubindage=None):
        """
        loop initial
        This method helps to create a tree menu easily
        the only thing you shulg prepare is a structure 
        with commands. The structure is dictionary-like.
        OrderedDict is menu list, dict is command description
        ##########
        Usage Example:
        ##########
        from collections import OrderedDict as oDict
        from tktools import TkTools
        ...
        class MyClass(TkTools, ...):
            ...
            def __init__(...):
                ...
                menu = oDict()
                menu["node1"] = oDict()
                # create a command
                menu["node1"]["command1"] = dict(...)
                # create a cascade as submenu
                menu["node1"]["subnode1"] = oDict() # subnode will be a cascade menu in main menu
                # create a command in submenu
                menu["node1"]["subnode1"]["command2"] = dict(...)
                # and so on
                ...
                self._create_menu(menu)
        ##########
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



