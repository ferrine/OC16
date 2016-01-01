# OC16
Этот проект связан с созданием скрипта для рассадки на [Открытом Чемпионате школ по экономике в МГУ](http://openchampionship.ru/).

Сделана первичная инициализация аудитории с полной проверкой адекватности входных значений
Сделаны методы выставки, изъятия/вставки участников, проверки их окружения на основе правил(школа, класс)

# Модули
## excelprocessor/
Библиотека предназначена для первичной обработки входных данных в программу. На данный момент реализована возможность преобразовывать таблицы, расположенные внутри таблицы в словарь из матриц. Пока что этой функциональности достаточно для перехода к следующему этапу разработки, а именно, реализации класса аудиторий.

### reader
Основная функция, которую предоставляет модуль, это `splitter(table, named=false)` она разбивает входную таблицу на словарь из матриц. Функция используется скриптом `splitter.py` и конструктором класса аудиторий.

### writer
В этом модуле будут расположены средства вывода информации. На данный момент там присутствуют вспомогательные классы потоков для `splitter.py`.

# Bonus
## Splitter.py
Этот скрит пользуется библиотекой excelprocessor и может применяться в повседневном пользовании решая проблему разбиения листа эксель с множеством таблиц на одной странице. Эти таблицы можно пометить метками в верхнем левом краю, рядом/в угловой ячейке. 

Более подробное руководство по использованию скрипта:
```
usage: splitter.py [-h] [-d] [-n] [-s {std,excel}] [-f FILE]
                   [input [input ...]]

This program allows you to parse excel documents and split multiple sequences
to different tables or sheets. It is also possible to name them depending on
the mark of the table. You can choose stream in {std, excel}. If you want
single file output it is possible to stream output into it. See more
information below.

positional arguments:
  input                 name of the file that you want to split should have
                        .xlsx extension

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           this flag allows to make a log file
  -n, --named           name every table, or excel sheet with a mark as top
                        left side cell
  -s {std,excel}, --stream {std,excel}
                        where to store the results, std by default
  -f FILE, --file FILE  if you want to store all results in one excel book?
                        name it
```
