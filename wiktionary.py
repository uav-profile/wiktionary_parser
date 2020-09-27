import sys
import os
import sqlite3
import requests
from bs4 import BeautifulSoup  # + lxml

PREFIX_WIKTIONARY = 'https://ru.m.wiktionary.org/wiki/'
PREF_WIKTIONARY = 'https://ru.wiktionary.org'
PAGE_LANGS = "https://ru.wiktionary.org/wiki/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%90%D0%BB%D1%84%D0%B0%D0%B2%D0%B8%D1%82%D0%BD%D1%8B%D0%B9_%D1%81%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D1%8F%D0%B7%D1%8B%D0%BA%D0%BE%D0%B2"

def _encode_to_percent(link):
    """ 
        Returns unicode strings (Russian, for example) in the so-called. percentage coding.
        That is, the link: https://ru.wikipedia.org/wiki/Россия
        Actually like this: https://ru.wikipedia.org/wiki/%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F
    Args:
        link (string): pass part of the link in Russian

    Returns:
        string: will return a formatted string
    
    -----------------------------------------------------------------
    [!] RUSSIAN:
        Возвращает unicode-строки (русские, например) в т.н.
        процентном кодировании.
        То есть ссылка https://ru.wikipedia.org/wiki/Россия
        На самом деле такая: https://ru.wikipedia.org/wiki/%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F
    Аргументы:
        link (строка): передайте часть ссылки на русском языке

    Возвращает:
        строка: вернется отформатированная строка
    """
    return requests.utils.quote(link)

def _parse_string_lang(str_):
    """
        The function takes a string, returns the pair 'language_name', 'number of words' 
        
    Args:
        str_ (string): string like 'Русский язык‎ (37 кат., 435973 с.)'

    Returns:
        string, string: a pair of strings like 'Русский_язык‎', '435973'
    
    -----------------------------------------------------------------
    [!] RUSSIAN:
        Функция принимает строку, возвращает пару 'название_языка', 'количество слов' 
        
    Аргументы:
        str_ (строка): строка вида 'Русский язык‎ (37 кат., 435973 с.)'

    Возвращает:
        строка, строка: пара строк вида 'Русский_язык‎', '435973'
    """
    lang_str = ""
    size = ""
    if str_.count("(") > 1:  # если в строке больше двух скобок '(' => 'Море (язык)‎ (3 кат., 27 с.)'
        num_digit = 0
        for i, letter in enumerate(str_):
            if letter.isdigit():
                num_digit = i
                break
        lang_str = str_[:num_digit-2]
        lang_str = lang_str.replace("\u200e","")  # убираем символ '\u200e'
        part_digits = str_[num_digit-1:]  # из строки забираем ее срез => '(3 кат., 27 с.)'
        part_digits = part_digits.replace("(","")  # убираем символ '('
        part_digits = part_digits.replace(")","")  # убираем символ ')'
        size = part_digits.split(",")[-1]  # разделяем строку по запятой: '3 кат.,27 с.' => ['3 кат.', '27 с.'] => '27 с.'
        size = size.replace("\xa0","")  # убираем нечитаемый символ '\xa0'
        size = size.replace("\n","")  # убираем нечитаемый символ '\n'
        size = size.replace(" с.","")  # убираем символы ' с.'
    else:
        lang_list_ = str_.split("(")  # делим строку на 2 части в список
        lang = "_".join(lang_list_[0].split())  # левую часть строки изменяем ''
        lang_str = lang.replace("\u200e","")  # получаем название языка с "_" вместо пробела:  'Русский язык‎' => 'Русский_язык‎'
        size_d = lang_list_[1]  # получаем вторую часть '37 кат., 435973 с.)'
        size_d = size_d.replace(")","")  # убираем символ ')'
        size_d = size_d.replace("\xa0","")  # убираем нечитаемый символ '\xa0'
        size_d = size_d.replace("\n","")  # убираем нечитаемый символ '\n'
        size = size_d.split(",")[-1].replace(" с.","")  # убираем символы ' с.'
    return lang_str, size

def _parse_page_words(link):
    """
        The function accesses the link, finds all the words on the page,
        looks for a link to the next page, and passes the list of words and the link.

    Args:
        link (string): string like 'https://ru.wiktionary.org/wiki/Русский_язык', with 'percentage' coding

    Returns:
        list, string: pair ([word list], link); if the page is last, then link = None
    
    -----------------------------------------------------------------
    [!] RUSSIAN:
        Функция обращается переходит по ссылке, обнаруживает все слова на странице,
        ищет ссылку на следующую страницу и передает список из слов и ссылку.

    Аргументы:
        link (строка): строка вида 'https://ru.wiktionary.org/wiki/Русский_язык', с 'процентным' кодированием

    Возвращает:
        список, строка: пара [список слов], ссылка; если страница последняя, то ссылка = None
    """
    global PREF_WIKTIONARY
    list_words = []
    new_link = None
    try:
        response = requests.get(link)  # получаем содержимое страницы
        soup = BeautifulSoup(response.text, 'lxml')
        soup_mw_pages = soup.find('div', {'id': 'mw-pages'})  # ищем теги
        soup_word_groups__ = soup_mw_pages.findAll('div', {'class': 'mw-category-group'})  # ищем теги
        for soup_word_groups in soup_word_groups__:  # цикл сохранения слов в список
            soup_word_groups_ = soup_word_groups.findAll('a')
            for soup_word in soup_word_groups_:
                word = soup_word.get_text()
                list_words.append(word)
        soup_hrefs = soup.findAll('a')
        for a in soup_hrefs:  # цикл для поиска ссылки на следующую страницу
            try:
                href = a.get("href")
                if href:
                    if a.get_text() == "Следующая страница":
                        new_link_part = a.get("href")
                        new_link = f"{PREF_WIKTIONARY}{new_link_part}"
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    return list_words, new_link

def _parse_word_page(link):
    """
        The function looks for the value of the passed word on the page
    
    Args:
        link (string): link

    Returns:
        string: word meaning (translation)
    -----------------------------------------------------------------
    [!] RUSSIAN:
        Функция ищет значение переданного слова на странице
    
    Аргументы:
        ссылка (строка): ссылка

    Возвращает:
        строка: значение слова (перевод)
    """
    word = "---"
    reserve_value = "---"
    response = requests.get(link)  # получаем содержимое страницы
    soup = BeautifulSoup(response.text, 'lxml')
    list__ = []
    try:
        soup_item = soup.find('div', {'class': 'mw-parser-output'})  # ищем теги
        soup_items = soup_item.findAll('ol')
        for i in soup_items:
            str_ = i.get_text()[:-1]
            list__.append(str_)
            if len(str_) > 1:  # если длина строки больше 1
                if "◆" in str_:  # данная ветка цикла сработает только если в ней будет символ '◆'
                    list_ = str_.split("◆")  # разделяем содержимое строки по этому символу
                    word = list_[0]  # забираем левую часть
                    word = word.strip()  # убираем пробелы справа и слева 
    except Exception as e:
        print(e)
    if word == "---":  #  если предыдущий цикл не отработал и не присвоил новое значение переменной 'word'
        try:
            soup_item = soup.find('div', {'class': 'mw-parser-output'})  # ищем теги
            soup_items = soup_item.findAll('p')  # ищем теги
            for s_items_child in soup_items:
                for child in s_items_child.recursiveChildGenerator():
                    list__.append(child)
                    if "title" in str(child):  # сработает только, если в теге <p> будет атрибут 'title', содержащий перевод слова
                        reserve_value = child.get_text()  # получаем перевод
        except Exception as e:
            print(e)
    if reserve_value != "---":  # если предыдущий цикл отработал, в 'word' передается значение
        word = reserve_value
    if word == "---":  # если предыдущие циклы не отработали
        try:  # перебираем тег <ol>
            soup_item = soup.find('div', {'class': 'mw-parser-output'})  # ищем теги
            soup_items = soup_item.findAll('ol')  # ищем теги
            for i in soup_items:
                str_ = i.get_text()
                list__.append(str_)
                if len(str_) > 1:  # если длина текста в тегах больше единицы 
                    word = str_
        except Exception as e:
            print(e)
    return word

def _get_page_languages(link):
    """
        The function returns a BeautifulSoup library object, 
        which is a list of languages that are on the page under the 'link'
    Args:
        link (string): html link, for example: 
                https://ru.wiktionary.org/wiki/Категория:Алфавитный_список_языков
                Warning: a link with Russian letters must be translated using 'percent' encoding.

    Returns:
        <class 'bs4.element.ResultSet'>: a list of languages is returned, you can iterate over it
    -----------------------------------------------------------------
    [!] RUSSIAN:
        Функция возвращает объект библиотеки BeautifulSoup,
        представляющий собой список языков, которые находятся
        на странице по ссылке 'link'
    Аргументы:
        link (строка): html-ссылка, например: 
                    https://ru.wiktionary.org/wiki/Категория:Алфавитный_список_языков
                    Предупреждение: ссылку с русскими буквами необходимо переводить при помощи 
                    'процентного' кодирования.

    Возвращает:
        <class 'bs4.element.ResultSet'>: возвращается список языков, можно по нему итерироваться
    """
    new_link = None
    try:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'lxml')
        soup_langs = soup.findAll('div', {'class': 'CategoryTreeItem'})
        soup_hrefs = soup.findAll('a')
        for a in soup_hrefs:
            try:
                href = a.get("href")
                if href:
                    if a.get_text() == "Следующая страница":
                        new_link_part = a.get("href")
                        new_link = f"https://ru.wiktionary.org{new_link_part}"
            except Exception as e:
                print(e)
        return "ok", soup_langs, new_link
    except Exception as e:
        return "error", str(e), None 

def _get_words(language = None, print_in_console = False, save_to_file = True, link = None):
    """
        The function takes a link to a page that contains a list of words.
        Saves and / or outputs a list of words and passes the link to the next page

    Args:
        language (string, optional): string like 'русский_язык'. Defaults to None.
        print_in_console (bool, optional): bool value => print or not print to console. Defaults to False.
        save_to_file (bool, optional): bool value => save or not save to file. Defaults to True.
        link (string, optional): link. Defaults to None.

    Returns:
        string: new link
    -----------------------------------------------------------------
    [!] RUSSIAN:
        Функция принимает ссылку на страницу, в которой имеется перечень слов.
        Сохраняет и/или выводит список слов и передает ссылку на следующую страницу

    Аргументы:
        language (строка, опционально): строка вида 'русский_язык'; по умолчанию - None.
        print_in_console (булевое значение, опционально): булевое значение => Печатать или не печатать в консоли; по умолчанию - False.
        save_to_file (булевое значение, опционально): булевое значение => Сохранять или не сохранять в файл; по умолчанию - True.
        link (строка, опционально): новая ссылка; по умолчанию - None.

    Возвращает:
        string: ссылка
    """
    new_link = None
    global PREFIX_WIKTIONARY
    try:
        words, new_link = _parse_page_words(link)
        if save_to_file:
            path_dicts = os.path.join(os.path.dirname(sys.argv[0]), "dictionaries")
            filename_new_dict = os.path.join(path_dicts, f"{language}.csv")
            counter = 1
            with open(filename_new_dict, "a+", encoding='utf-8') as csv:
                for word in words:
                    link = PREFIX_WIKTIONARY + _encode_to_percent(word)
                    translated_word = _parse_word_page(link)
                    if print_in_console:  # если print_in_console = True
                        if new_link:
                            print(f"{word} => {translated_word}")  # если в языке больше 200 слов, т.е. есть ссылка на след. страницу
                        else:
                            print(f"{counter}. {word} => {translated_word}")  # если слова закончились или всего их меньше 200, вывод с нумерацией
                    csv.write(f"{word};{translated_word}\n")
                    counter += 1
        else:
            counter = 1
            for word in words:
                link = PREFIX_WIKTIONARY + _encode_to_percent(word)
                translated_word = _parse_word_page(link)
                if print_in_console:  # если print_in_console = True
                    print(f"{counter}. {word} => {translated_word}")
                counter += 1
    except Exception as e:
        print(e)
    return new_link
    
def _contin_parse_page_words(lang, print_, save_):
    """
        The function saves and/or prints a list of words in the specified language

    Args:
        lang (string): Selected language, for example "Русский_язык"
        print_ (bool): Output/do not output to console
        save_ (bool): Save/not save to file
    
    -----------------------------------------------------------------
    [!] RUSSIAN:
        Функция сохраняет и/или выводит список слов в указанном языке

    Аргументы:
        lang (строка): выбранный язык, например "Русский_язык"
        print_ (булевое значение): выводить/не выводить в консоли
        save_ (булевое значение): сохранять/не сохранять в файл
    """
    global PREFIX_WIKTIONARY
    path_dicts = os.path.join(os.path.dirname(sys.argv[0]), "dictionaries")  # составляется абс. путь до каталога 'dictionaries' 
    filename_new_dict = os.path.join(path_dicts, f"{lang}.csv")  # составляется абс. путь до csv-файла в каталоге 'dictionaries'
    if os.path.exists(filename_new_dict):  # проверка на существование csv-файла 
        os.remove(filename_new_dict)  # если он имеется, будет удален
    if not os.path.exists(path_dicts):  # проверка на существование каталога 'dictionaries'  
        os.mkdir(path_dicts)  # если не существует, будет создан
    prcnt_code = _encode_to_percent(f"Категория:{lang}")  # перевод строки в процентное кодирование
    link = f"{PREFIX_WIKTIONARY}{prcnt_code}"  # составление первой ссылки для языка, далее новые будут созданы в цикле
    c = 200  # количество слов на 1 странице языка 
    while True:
        if link:
            new_link = _get_words(language=lang, print_in_console=print_, save_to_file=save_, link = link)
            print(f"---------------------------------loaded: {c}---------------------------------")  # удобнее отслеживать работу
            link = new_link
            c += 200
        else:
            print("\nСкрипт завершил свою работу")
    
def make_dictionary(lang, csv = False, print_to_console = False):
    """
        The main function that creates the dictionary of the language.

    Args:
        lang (string): Language name, for example 'Русский_язык'
        csv (bool, optional): save/not save to file. Defaults to False.
        print_to_console (bool, optional): print/do not print to console. Defaults to False.
    -----------------------------------------------------------------
    [!] RUSSIAN:
        Главная функция, которая создает словарь языка.

    Аргументы:
        lang (строка): имя языка, например 'Русский_язык'
        csv (булевое значение, опционально): сохранять/не сохранять в файл; по умолчанию - False.
        print_to_console (булевое значение, опционально): выводить/не выводить в консоли; по умолчанию - False.
    """
    if lang:
        _contin_parse_page_words(lang=lang, print_ = print_to_console, save_= csv)
    else:
        print("Вы не выбрали язык")

def get_languages(lang_base = "languages.txt", mode = "read"):
    """
        The function refers to the global variable 'PAGE_LANGS', which contains 
        a link to the main Wiktionary page. If successful, the function prints all 
        existing languages on the site to the console. 2 modes: reading from a file 
        and writing to this file with output.

    Args:
        lang_base (str, optional): name of the file with languages. Defaults to "languages.txt".
        mode (str, optional): operating modes: 'write', 'read'. Defaults to "read".

    Returns:
        list: returns a list with tuples of languages => [('Русский_язык', 435973), ('Украинский_язык', 94168),...]
    
    -----------------------------------------------------------------
    [!] RUSSIAN:
        Функция обращается к глобальной переменной 'PAGE_LANGS', которая содержит ссылку
        на главную страницу Викисловаря. При успешном исходе функция печатает в консоли 
        все существующие на сайте языки. 2 режима: чтение из файла и запись в этот файл с выводом.

    Аргументы:
        lang_base (str, опционально): имя файла с языками. Defaults to "languages.txt".
        mode (str, опционально): режимы работы: 'write', 'read'. Defaults to "read".

    Возвращает:
        list: возвращает список с кортежами языков => [('Русский_язык', 435973), ('Украинский_язык', 94168),...]
    """
    global PAGE_LANGS
    langs_list_ = []
    langs_list_2 = []
    link = PAGE_LANGS
    if mode == "read":
        with open(lang_base, "r", encoding='utf-8') as f:
            text = f.readlines()
            for str_ in text:
                if "language" not in str_:
                    lang_str, size = str_.split(";")
                    langs_list_.append((lang_str, (size.replace("\n",""))))
            return langs_list_
    elif mode == "write":
        if os.path.exists(lang_base):
            os.remove(lang_base)
        status = ""
        while True:
            if link:
                status, langs_list_temp, link = _get_page_languages(link = link)
                if status == "ok":
                    for soup_lang in langs_list_temp:
                        str_ = soup_lang.get_text()
                        if str_ != "":
                            str_ = str_[3:]
                            label, size = _parse_string_lang(str_)
                            langs_list_2.append((label, int(size)))
                        else:
                            pass
                    langs_list_ = langs_list_ + langs_list_2
                elif status == "error":
                    print("Error:", langs_list_temp)
            else:
                break
        langs_list_ = list(set(langs_list_))
        langs_list_ = sorted(langs_list_, key = lambda x: (-(x[-1]), x[0]))
        with open(lang_base, "a+", encoding='utf-8') as f:
            f.write("language;amount\n")
            try:
                for lang in langs_list_:
                    f.write(f"{lang[0]};{lang[1]}\n")
            except Exception as e:
                print(e)
    else:
        print("in 'get_languages': arg 'mode' => ['read', 'write']")
    return langs_list_

if __name__ == "__main__":
    if sys.argv[1]:
        make_dictionary(lang = sys.argv[1], csv=True, print_to_console=True)
    else:
        print("1st argument -> 'language_name'; RUS: передайте после названия скрипта язык...\n \
        например: python wiktionary.py \"Испанский_язык\"")