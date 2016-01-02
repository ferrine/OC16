from auditory import Auditory
from excelprocessor.reader import splitter
import pandas as pd
from check_system import Checker
import random
from rassadka_exceptions import *


def clr(x):
    try:
        return x.strip()
    except AttributeError:
        return x

goodpath = "exceltestdata/auditories.xlsx"
people = pd.read_excel("exceltestdata/people.xlsx", sheetname=0).applymap(lambda x: clr(x))
people.columns = ["id", "fam", "name", "otch", "town", "school", "team", "klass"]
people["klass"] = people["klass"].apply(lambda x: int(x.split()[0]))
people.set_index("id")
good_settings = pd.read_excel(goodpath, header=None, sheetname="Общие настройки")
good_set = splitter(good_settings, True)
Checker.global_init(good_set)
good_settings = pd.read_excel(goodpath, header=None, sheetname="П1")
good_set = splitter(good_settings, True)
a = Auditory(good_set, "П1")
records = people.to_dict(orient="records")
random.shuffle(records)
try:
    for person in records:
        a.rand_insert(person)
except EndLoopException:
    print("End of Loop\n")
finally:
    message = """
capacity: {0}
placed:   {1}
allowed:
{2}
""".format(a.capacity, a.counter, a.checker.allowed)
    print(message)
    print(a.m, file=open("rand_test_out.txt", "w"))

print("-"*20 + "\n")

good_set = splitter(good_settings, True)
a = Auditory(good_set, "П1")

