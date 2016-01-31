# OC16
Этот проект связан с созданием скрипта для рассадки на [Открытом Чемпионате школ по экономике в МГУ](http://openchampionship.ru/).

Текущая версия программы позволяет выполнять почти все задачи в ходе рассадки и проведения мероприятия.

А именно:

* Загрузка настроек и аудиторий
* Добавление, удаление аудиторий
* Изменение общих и аудиторных настроек
* Получение актуальной информации по рассадке, выгрузок для печати и анализа
* Фиксирование участников на местах
* Рассадка, досадка, изъятие участников, обновление их информации
  
# Инструкции
Для корректного запуска программы необходимо правильно заполнить лист с настройками. Образец: `samples\settings.xlsx`
Загружать людей необходимо с полной информацией с следующими полями `email|Фамилия|Имя|Отчество|Город|Команда|Класс`
Для операций обновления информации по местам, необходимо добавить к этим полям еще `|Аудитория|Ряд|Место`. Однако, для обновления информации по email допускается не добавлять эти поля. Если какого-то участника нету, то это повлечет ошибку, так что лучше убелиться, что все участники сидят.
Фиксирование(блокировка) участников на местах позволяет ограничить изменение блокируемого места с участником, для удаления строго, для обновления нестрого.

# Bonus
## splitter.py
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
