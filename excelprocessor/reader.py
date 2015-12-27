import pandas as pd
import numpy as np


def split_by(table, _output, clean, axes=False, named=False, *, logfile=None):
    """

    argument named: именовать ли таблицы? (в таком случае будет взята верхняя левая ячейка как имя)
    argument _output: куда выводить чистые табицы
    type table: Pandas DataFrame
    arg clean: насколько чиста таблица? [чисто по Y, чисто по X]
    argument axes: column?
    """
    assert type(table) is pd.DataFrame, "К сожалению, функция работает только с pandas.DataFrame"
    if min(table.shape) <= 1:  # не обрабатываем "нетаблицы"
        if logfile:
            logfile.write("Table has bad shape [" + str(table.shape) + "]\n" )
            logfile.write(str(table) + "\n")
        return
    parse_list = []
    to_slise = []
    clean[axes] = True  # Использую прием, что по индексу axes я меняю только текущую итерацию, при первом прогоне полюбому пройдет второй
    if logfile:
        logfile.write("Checking: " + str(range(table.shape[axes])) +"\n")
    for i in range(table.shape[axes]):
        if logfile:
            logfile.write(str((table.iloc[:, i] if axes else table.iloc[i, :]).values) +"\n")
        if not np.all(pd.isnull((table.iloc[:, i] if axes else table.iloc[i, :]))):     # если строка/столбец не пустая, то возвращает Ложь
            to_slise.append(i)
            if logfile:
                logfile.write({0: "Row ", 1: "Col "}[axes] + str(i) +
                      "\t is not empty and to_slise = " + str(to_slise) + "\n" +
                      "-"*10 +"\n")
        else:
            clean = [False, False]  # Если что-то не так, надо прогнать еще два раза
            if to_slise:
                if logfile:
                    logfile.write("Appending: " + str(to_slise) +"\n")
                parse_list.append((table.iloc[:, to_slise] if axes else table.iloc[to_slise, :]))
                to_slise = []
            if logfile:
                logfile.write({0: "Row ", 1: "Col "}[axes] + str(i) + "\t is empty and to_slise = " + str(to_slise) + "\n" +
                      "-"*10 +"\n")
    else:
        if to_slise:
            if logfile:
                logfile.write("Appending: " + str(to_slise) +"\n")
            parse_list.append((table.iloc[:, to_slise] if axes else table.iloc[to_slise, :]))
    if clean[0] and clean[1]:  #Проверим, отчистили ли мы эту таблицу
        move_x = int(np.all(pd.isnull(parse_list[0].iloc[1:, 0])))  # Проверяем крайние левый и верхний ряд, тк там
        move_y = int(np.all(pd.isnull(parse_list[0].iloc[0, 1:])))  # может быть имя и надо удалять пустоты
        if logfile:
            logfile.write("x " + "-"*20 + "\n" + str(parse_list[0].iloc[:, 0]) +"\n")
            logfile.write("y " + "-"*20 + "\n" + str(parse_list[0].iloc[0, :]) +"\n")
            logfile.write("x : " + str(move_x) + "\t y: " + str(move_y) +"\n")
        if named:
            name = parse_list[0].iloc[0, 0]
        else:
            name = len(_output)
        _output[name] = parse_list[0].iloc[move_y:, move_x:].as_matrix()
    elif parse_list:  # Таблица не чиста, прогоняем все для тех, что выделились или продолжаем очищать единственную
        for item in parse_list:
            if logfile:
                logfile.write("Clean for item is: " + str(clean) + "\n" + str(item) +"\n")
            split_by(item, _output=_output, axes=(not axes), named=named, clean=clean, logfile=logfile)



def splitter(table, named=False, *, debug=False):
    """
    Функция позволяет разбить сырую таблицу pandas,
    которая содержит дочерние таблицы, на несколько,
    и поместить их матрицы в словарь. Далее, матрицы
    можно использовать по своему усмотрению.
    Возможна поддержка тегов. Для этого надо
    именовать таблицу слева сверху любой меткой,
    она будет ключем в словаре, нумерация иначе.
    Чтобы использовать эту функцию надо поставить
    named=True, по умолчанию False.
    """
    if debug:
        log = open("log.txt", "w")
    else:
        log = None
    result = dict()
    split_by(_output=result, table=table, logfile=log, clean=[False, False], named=named)
    if debug:
        log.close()
    return result










