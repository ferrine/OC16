from auditory import *
import os
from collections import OrderedDict as oDict
from excelprocessor.reader import splitter
from check_system import Checker

if __name__ == "__main__":
    # Обновить debug.txt
    debugfile = RassadkaException.lg
    if os.path.isfile(debugfile):
        os.remove(debugfile)
        print(debugfile + " updated")
    goodpath = "exceltestdata/auditories.xlsx"
    bad_general = "exceltestdata/bad_auditories_general.xlsx"
    bad_specific = "exceltestdata/bad_auditories_specific.xlsx"
    bad_values1 = "exceltestdata/bad_auditories_values.xlsx"
    bad_values2 = "exceltestdata/bad_auditories_values2.xlsx"
    bad_shape = "exceltestdata/bad_auditories_shape.xlsx"
    # init test
    bad_conditions = oDict([("general", bad_general),
                           ("specific", bad_specific),
                           ("values1", bad_values1),
                           ("values2", bad_values2),
                           ("shape", bad_shape)])
    for stress, path in bad_conditions.items():
        bad_settings = pd.read_excel(path, header=None, sheetname="П1")
        bad_set = splitter(bad_settings, True)
        try:
            bad = Auditory(bad_set, stress)
        except RassadkaException:
            print("caught {0}".format(stress))
    print("\nТест с аудиториями закончился\n")
    good_settings = pd.read_excel(goodpath, header=None, sheetname="Общие настройки")
    good_set = splitter(good_settings, True)
    Checker.global_init(good_set)
    good_settings = pd.read_excel(goodpath, header=None, sheetname="П1")
    good_set = splitter(good_settings, True)
    a = Auditory(good_set, "П1")
    print(a)
    print(a.m, file=open("out.txt", "w"))
    print("\n{0}".format(a.capacity))
