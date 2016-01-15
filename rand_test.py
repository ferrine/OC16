import random

import pandas as pd
from rassadka_modules.auditory import Auditory

from rassadka_modules.check_system import Checker
from rassadka_modules.excelprocessor.reader import splitter
from rassadka_modules.rassadka_exceptions import *


def clr(x):
    try:
        return x.strip()
    except AttributeError:
        return x

prefix = "test_out\\"

goodpath = "exceltestdata/auditories.xlsx"
people = pd.read_excel("exceltestdata/people.xlsx", sheetname=0).applymap(clr)
people.columns = ["id", "fam", "name", "otch", "town", "school", "team", "klass"]
people["klass"] = people["klass"].apply(lambda x: int(x.split()[0]))
people.set_index("id")
good_settings = pd.read_excel(goodpath, header=None, sheetname="Общие настройки")
good_set = splitter(good_settings, True)
Checker.raw_global_init(good_set)
good_settings = pd.read_excel(goodpath, header=None, sheetname="П1")
good_set = splitter(good_settings, True)
a = Auditory(good_set, "П1")
records = people.to_dict(orient="records")
random.shuffle(records)

print("-"*20 + "\n")
print("All in one\n")
print(a.team_rand_insert(records))
print(a.summary())

print("-"*20 + "\n")

print("One by one")
try:
    for person in records:
        a.rand_insert(person)
except EndLoopException:
    print("End of Loop\n")
finally:
    for rec in a.get_all_seated():
        print(rec)
    print("Тут сажались без разбору")
    print(a.summary())
    print(a.m, file=open(prefix + "rand_test_out.txt", "w"))
