import pandas as pd
from auditory import Auditory

from rassadka_modules.check_system import Checker
from rassadka_modules.excelprocessor import splitter
from rassadka_modules.rassadka_exceptions import CheckIsFalse

goodpath = "exceltestdata/auditories.xlsx"


def clr(x):
    try:
        return x.strip()
    except AttributeError:
        return x
# Короч дальше надо делать тест на правильную проверку в классе аудитории
people = pd.read_excel("exceltestdata/test_people.xlsx", sheetname=0).applymap(lambda x: clr(x))
people.columns = ["id", "fam", "name", "otch", "town", "school", "team", "klass"]
people["klass"] = people["klass"].apply(lambda x: x.split()[0])
good_settings = pd.read_excel(goodpath, header=None, sheetname="Общие настройки")
good_set = splitter(good_settings, True)
Checker.raw_global_init(good_set)
good_settings = pd.read_excel(goodpath, header=None, sheetname="П1")
good_set = splitter(good_settings, True)
a = Auditory(good_set, "П1")
# 1,2 = center, surrounding = 0, 10, 18, for check 26
a.insert((1, 1), people.iloc[0].to_dict())
a.insert((1, 3), people.iloc[0].to_dict())
a.insert((0, 1), people.iloc[10].to_dict())
a.insert((0, 2), people.iloc[10].to_dict())
a.insert((0, 3), people.iloc[18].to_dict())
a.insert((2, 1), people.iloc[18].to_dict())
a.insert((2, 2), people.iloc[0].to_dict())
a.insert((2, 3), people.iloc[10].to_dict())
print("True -> ", a.scan((1, 2), people.iloc[26].to_dict()))
try:
    a.scan((1, 2), people.iloc[10].to_dict())
except CheckIsFalse:
    print("Check is False as supposed")



