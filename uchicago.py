# -*- coding: utf-8 -*-
# Author: U.A.V.
# 2021-03
# License : MIT


import os
import re
import time
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import random
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json

MAIN_URL = "https://dsal.uchicago.edu/cgi-bin/app/hayyim_query.py?page="
MAIN_URL2 = "https://dsal.uchicago.edu/cgi-bin/app/steingass_query.py?page="


user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)', ]

eng_charact = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    '(', ]

parts_of_speech_g = [
    'intransitive verb', 'ajective-noun', 'transitive verb', 'past participle; passive participial adjective',
    'numeral adjective', 'adverbial conjunction', 'interrogative pronoun', 'plural', 'adjectives',
    'transitive and intransitive verb', 'conjunction', 'preposition', 'common error allowed by usage',
    'independent adverb', 'interrogative adjective', 'relative pronoun', 'intransitive and transitive',
    'reflexive pronoun', 'independant adverb', 'interjection', 'adjective',
    'inseparable pronoun, pronominal ending', 'intransitive verb, adjective', 'active participial adjective',
    'adjective-noun', 'noun', 'adverb', 'verb', 'pronoun', ]


def has_latin_character(str_to_check):
    for i in str_to_check.upper():
        if i in eng_charact and i != '(':
            return True
    return False


def get_origin_word(str_to_origin):
    word_to_return = ''
    for idx, i in enumerate(str_to_origin.strip()):
        if i not in eng_charact:
            word_to_return += i
        else:
            if idx == 0 and i == '(':
                word_to_return += i
            else:
                break
    if ' ' in word_to_return:
        word_to_return = word_to_return.strip()
    return word_to_return


def get_items(url):
    r = requests.get(url, headers={'User-Agent': random.choice(user_agents)})
    with open(f'html/{url.split("?")[-1]}.html', 'wt', encoding='utf-8') as f:
        f.write(r.text)
    soup = BeautifulSoup(r.content, 'lxml')
    version_soup = soup.find('td', {'class': 'turner', 'align': 'center'})
    if version_soup:
        version_ = version_soup.getText().strip()
        if 'V1' in version_:
            version_item = 'V1'
        elif 'V2' in version_:
            version_item = 'V2'
        else:
            version_item = '?'
    soup_content = soup.find('div', {'class': 'hw_result'})
    soup_div = soup_content.findAll('div')
    items_list = []
    for i in soup_div:
        try:
            text_ = str(i).replace('<br/>', '</br>')
            rows = text_.split("</br>")
            for row in rows:
                soup_item = BeautifulSoup(row, 'lxml')
                origin_item_temp, origin_item, part_item, part_pn_item = None, None, None, None
                text_item = soup_item.getText().strip()
                try:
                    # Если есть тег <hw>, где указано слово
                    origin_item = soup_item.find('hw').getText().strip()
                    origin_item_temp = soup_item.find('hw').getText().strip()
                except:
                    origin_item = get_origin_word(soup_item.getText().lstrip())
                    origin_item_temp = get_origin_word(
                        soup_item.getText().lstrip())
                part_pn_soup = soup_item.find('pn')
                if part_pn_soup:
                    part_pn_item = part_pn_soup.getText()
                    origin_item = part_pn_item + ' ' + origin_item
                    origin_item_temp += ' ' + part_pn_item
                part_soup = soup_item.find('part')
                if part_soup:
                    part_item = part_soup.getText()
                    text_item = text_item.replace(part_item, '')
                text_item = text_item.replace(
                    origin_item_temp, '').strip().replace('  ', ' ')
                if '=' in origin_item:
                    origin_item_list = origin_item.split('=')
                    origin_item = origin_item_list[0].rstrip()
                    text_item = '= ' + \
                        origin_item_list[1].strip() + ' ' + text_item
                items_list.append(
                    {'word': origin_item, 'part': part_item, 'dict': version_item, 'text': text_item})
        except Exception as e:
            print(e)
    return items_list


def get_items_local(file):
    r = ''
    with open(file, 'rt', encoding='utf-8') as f:
        r = f.read()
    soup = BeautifulSoup(r, 'lxml')
    version_soup = soup.find('td', {'class': 'turner', 'align': 'center'})
    if version_soup:
        version_ = version_soup.getText().strip()
        if 'V1' in version_:
            version_item = 'V1'
        elif 'V2' in version_:
            version_item = 'V2'
        else:
            version_item = '?'
    soup_content = soup.find('div', {'class': 'hw_result'})
    soup_div = soup_content.findAll('div')
    items_list = []
    part_of_speech_list = []
    for i in soup_div:
        try:
            text_ = str(i).replace('<br/>', '</br>')
            rows = text_.split("</br>")
            for row in rows:
                soup_item = BeautifulSoup(row, 'lxml')
                origin_item_temp, origin_item, part_item, part_pn_item, text_item_temp = None, None, None, None, ''
                text_item_temp = soup_item.getText().strip()
                try:
                    # Если есть тег <hw>, где указано слово
                    origin_item = soup_item.find('hw').getText().strip()
                    origin_item_temp = origin_item
                except:
                    origin_item = get_origin_word(soup_item.getText().lstrip())
                    origin_item_temp = origin_item
                if origin_item_temp.strip() == text_item_temp:
                    # with open('deviant.csv', 'at+', encoding='utf-8') as f_d:
                    #     f_d.write(text_item_temp + '\n')
                    # СЛУЧАЙ, КОГДА В ЗНАЧЕНИЕ СЛОВА ЗАПИСАНО ВСЁ.
                    # ТО ЕСТЬ ВСЯ СТРОКА ПОЛУЖИРНАЯ
                    origin_item = get_origin_word(text_item_temp)
                    text_item = text_item_temp.replace(origin_item, '')
                    text_item = text_item_temp.replace(
                        origin_item_temp, '').strip().replace('  ', ' ')
                    for ps in parts_of_speech_g:
                        if ps in text_item.lower():
                            part_item = ps
                            break
                else:
                    part_pn_soup = soup_item.find('pn')
                    if part_pn_soup:
                        part_pn_item = part_pn_soup.getText()
                        origin_item = part_pn_item + ' ' + origin_item
                        origin_item_temp += ' ' + part_pn_item
                    part_soup = soup_item.find('part')
                    if part_soup:
                        part_item = part_soup.getText()
                        text_item_temp = text_item_temp.replace(part_item, '')
                    text_item = text_item_temp.replace(
                        origin_item_temp, '').strip().replace('  ', ' ')
                    if '=' in origin_item:
                        origin_item_list = origin_item.split('=')
                        origin_item = origin_item_list[0].rstrip()
                        text_item = '= ' + \
                            origin_item_list[1].strip() + ' ' + text_item
                # работаем с частью речи, удаляю лишнее, привожу к норм. виду
                if part_item:
                    part_item = part_item.lower()
                    if part_item == 'intransitive verbadjective':
                        part_item = 'intransitive verb, adjective'
                    elif part_item == 'noun-adjective':
                        ...
                    elif part_item == 'adverb-adjective':
                        ...
                    elif part_item == 'etc; and so forth':
                        part_item = '-'
                    elif part_item == 'noun>':
                        part_item = 'noun'
                    elif part_item == 'noun\ufeff':
                        part_item = 'noun'
                    elif part_item == 't ransitive verb':
                        part_item = 'transitive verb'
                    elif part_item == 'nou\ufeff watch(ing),':
                        part_item = 'noun'
                    elif part_item == 'snoun':
                        part_item = 'noun'
                    elif part_item == 'interrogative adjective>':
                        part_item = 'interrogative adjective'
                    elif part_item == 'transitive and intransitive verbd':
                        part_item = 'transitive and intransitive verb'
                    elif part_item == 'intransitive and transitive verb':
                        part_item = 'transitive and intransitive verb'
                items_list.append(
                    {'word': origin_item, 'part': part_item, 'dict': version_item, 'text': text_item})
        except:
            pass
    return items_list


def get_items_local_steingass(file):
    r = ''
    with open(file, 'rt', encoding='utf-8') as f:
        r = f.read()
    soup = BeautifulSoup(r, 'lxml')
    soup_content = soup.find('div', {'class': 'hw_result'})
    soup_div = soup_content.findAll('div')
    items_list = []
    part_of_speech_list = []
    for i in soup_div:
        origin, pronounce, text, lang = '', '', '', ''
        try:
            lang_soup = i.find('lang')
            if lang_soup:
                lang = lang_soup.getText()
            hw_soup = i.find('hw')
            origin_soup = hw_soup.find('pa')
            if origin_soup:
                origin = origin_soup.getText().strip()
            pronounce_soup = hw_soup.find('i')
            if pronounce_soup:
                pronounce = pronounce_soup.getText().strip()
            text = i.getText()
            text = text.replace(origin, '')
            text = text.replace(pronounce, '')
            text = text.strip()
            if text[0] == lang:
                text = text[1:]
            text = text.strip()
            if text[0] == ',':
                text = text[1:]
            items_list.append(
                {'word': origin, 'pronounce': pronounce, 'text': text})
        except:
            pass

    return items_list


def parse_dictionary(filename):
    # записываю шапку (родителя xml-дерева)
    data = ET.Element('xml', language='persian',
                      url='https://dsal.uchicago.edu/cgi-bin/app/hayyim_query.py?page=XXXX')
    mydata = ET.tostring(data, encoding='unicode', method='xml')
    with open(f"{filename}.xml", "wt", encoding='utf-8') as f:
        f.write(mydata)
    # парсим с сайта, пишем это в список, сделана конструкция для удобства,
    # для быстродействия можно запись осуществлять сразу в функции get_items()
    list_to_json = []
    tree = ET.parse('persian.xml')
    root = tree.getroot()
    for i in range(1, 2260):
        try:
            list_ = get_items(f"{MAIN_URL}{i}")
            list_to_json += list_
            for it_word in list_:
                element = root.makeelement('word', {})
                element2 = element.makeelement('eng', {})
                element2.set('original', it_word['word'])
                if it_word['part']:
                    element2.set('part_of_speech', it_word['part'])
                else:
                    element2.set('part_of_speech', '-')
                element2.set('version_of_dictionary', it_word['dict'])
                element2.text = it_word['text']
                element.append(element2)
                root.append(element)
        except Exception as e:
            with open('errors.txt', 'wt+', encoding='utf-8') as f:
                f.write(f"Ошибочка: {e}, {MAIN_URL}{i}\n")
    # сохранение в xml
    tree.write(f'{filename}.xml', encoding='utf-8')
    # сохранение в json
    with open(f"{filename}.json", 'wt', encoding='utf-8') as f:
        json.dump(list_to_json, f, ensure_ascii=False)


def extract_translations_form_string(getting_string):
    # формат: 1. какой-то текст 2. текст2 => ['какой-то текст', 'текст2']
    pattern = r"\d. (\D{0,})"
    result = re.findall(pattern, getting_string)
    return result


def make_pretty_xml(not_abs_filename):
    e = ''
    with open(f'{not_abs_filename}.xml', 'rt', encoding='utf-8') as f:
        e = f.read()

    e = e.replace('<word>', '\n<word>')
    e = e.replace('</word>', '\n</word>')
    e = e.replace('<eng', '\n\t<eng')
    e = e.replace('</eng', '\n\t</eng')
    e = e.replace('<pers', '\n\t<pers')
    e = e.replace('</pers', '\n\t</pers')

    e = e.replace("&amp;", "&")
    e = e.replace('&gt;', '')

    with open(f'_{not_abs_filename}.xml', 'wt', encoding='utf-8') as f:
        f.write(e)


def parse_dictionary_local_hayyim(filename):
    words_counter = 0
    counter1, counter2 = 0, 0
    start_time = time.time()
    # записываю шапку (родителя xml-дерева)
    data = ET.Element('xml', language='persian',
                      url='https://dsal.uchicago.edu/cgi-bin/app/hayyim_query.py?page=XXXX')
    mydata = ET.tostring(data, encoding='unicode', method='xml')
    with open(f"{filename}_deviant.xml", "wt", encoding='utf-8') as f:
        f.write(mydata)
    with open(f"{filename}.xml", "wt", encoding='utf-8') as f:
        f.write(mydata)
    # парсим с сайта, пишем это в список, сделана конструкция для удобства,
    # для быстродействия можно запись осуществлять сразу в функции get_items()
    #list_to_json = []
    tree = ET.parse(f'{filename}.xml')
    root = tree.getroot()
    tree_devi = ET.parse(f'{filename}_deviant.xml')
    root_devi = tree_devi.getroot()
    pbar = tqdm(total=len(os.listdir('html_hayyim')))
    for f_ in os.listdir('html_hayyim'):
        try:
            list_ = get_items_local(f'html_hayyim/{f_}')
            # list_to_json += list_
            for it_word in list_:
                words_counter += 1
                # Когда встречаются все арабские
                if not has_latin_character(it_word['word']):
                    counter1 += 1
                    element = root.makeelement('word', {})
                    element2 = element.makeelement('pers', {})
                    element2.set('original', it_word['word'].strip())
                    element2.set('volume', it_word['dict'])
                    element2.set('dictionary', 'hayyim')
                    page_ = f_.split('.')[0].split('=')[-1]
                    element2.set('page', page_)
                    # работаем с переводом
                    extract_list = extract_translations_form_string(
                        it_word['text'].strip())
                    element3 = element.makeelement('eng', {})
                    if len(extract_list) == 0:
                        element3.set('translate1', it_word['text'].strip())
                    elif len(extract_list) == 1:
                        element3.set('translate1', extract_list[0].strip())
                    elif len(extract_list) == 2:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                    elif len(extract_list) == 3:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                    elif len(extract_list) == 4:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                        element3.set('translate4', extract_list[3].strip())
                    elif len(extract_list) == 5:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                        element3.set('translate4', extract_list[3].strip())
                        element3.set('translate5', extract_list[4].strip())
                    elif len(extract_list) == 6:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                        element3.set('translate4', extract_list[3].strip())
                        element3.set('translate5', extract_list[4].strip())
                        element3.set('translate6', extract_list[5].strip())
                    elif len(extract_list) == 7:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                        element3.set('translate4', extract_list[3].strip())
                        element3.set('translate5', extract_list[4].strip())
                        element3.set('translate6', extract_list[5].strip())
                        element3.set('translate7', extract_list[6].strip())
                    elif len(extract_list) == 8:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                        element3.set('translate4', extract_list[3].strip())
                        element3.set('translate5', extract_list[4].strip())
                        element3.set('translate6', extract_list[5].strip())
                        element3.set('translate7', extract_list[6].strip())
                        element3.set('translate8', extract_list[7].strip())
                    if it_word['part']:
                        element2.set('part_of_speech', it_word['part'])
                    else:
                        element2.set('part_of_speech', '')
                    element.append(element2)
                    element.append(element3)
                    root.append(element)
                else:   # Когда встречаются латинские -> ВЫБРОС
                    counter2 += 1
                    element = root_devi.makeelement('word', {})
                    element2 = element.makeelement('pers', {})
                    element2.set('original', it_word['word'].strip())
                    element2.set('volume', it_word['dict'])
                    element2.set('dictionary', 'hayyim')
                    page_ = f_.split('.')[0].split('=')[-1]
                    element2.set('page', page_)
                    extract_list = extract_translations_form_string(
                        it_word['text'].strip())
                    element3 = element.makeelement('eng', {})
                    if len(extract_list) == 0:
                        element3.set('translate1', it_word['text'].strip())
                    elif len(extract_list) == 1:
                        element3.set('translate1', extract_list[0].strip())
                    elif len(extract_list) == 2:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                    elif len(extract_list) == 3:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                    elif len(extract_list) == 4:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                        element3.set('translate4', extract_list[3].strip())
                    elif len(extract_list) == 5:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                        element3.set('translate4', extract_list[3].strip())
                        element3.set('translate5', extract_list[4].strip())
                    elif len(extract_list) == 6:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                        element3.set('translate4', extract_list[3].strip())
                        element3.set('translate5', extract_list[4].strip())
                        element3.set('translate6', extract_list[5].strip())
                    elif len(extract_list) == 7:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                        element3.set('translate4', extract_list[3].strip())
                        element3.set('translate5', extract_list[4].strip())
                        element3.set('translate6', extract_list[5].strip())
                        element3.set('translate7', extract_list[6].strip())
                    elif len(extract_list) == 8:
                        element3.set('translate1', extract_list[0].strip())
                        element3.set('translate2', extract_list[1].strip())
                        element3.set('translate3', extract_list[2].strip())
                        element3.set('translate4', extract_list[3].strip())
                        element3.set('translate5', extract_list[4].strip())
                        element3.set('translate6', extract_list[5].strip())
                        element3.set('translate7', extract_list[6].strip())
                        element3.set('translate8', extract_list[7].strip())
                    if it_word['part']:
                        element2.set('part_of_speech', it_word['part'])
                    else:
                        element2.set('part_of_speech', '')
                    element.append(element2)
                    element.append(element3)
                    root_devi.append(element)
        except Exception as e:
            with open('errors.txt', 'at+', encoding='utf-8') as f:
                f.write(f"Ошибочка: {e}, {f_}\n")
        pbar.update(1)
    pbar.close()
    # сохранение в xml
    tree.write(f'{filename}.xml', encoding='utf-8')
    tree_devi.write(f'{filename}_deviant.xml', encoding='utf-8')

    # сохранение в json
    # with open(f"{filename}.json", 'wt', encoding='utf-8') as f:
    #     json.dump(list_to_json, f, ensure_ascii=False)

    # make_pretty_xml(filename)
    #make_pretty_xml(filename + '_deviant')
    # print("GOOD. THAT'S ALL")
    print("Выполнено за : %s сек. Всего %s слов" %
          (time.time() - start_time, words_counter))
    print("Арабские слова: %s, смешанные слова: %s" %
          (counter1, counter2))


def parse_dictionary_local_steingass(filename):
    words_counter = 0
    start_time = time.time()
    # записываю шапку (родителя xml-дерева)
    data = ET.Element('xml', language='persian',
                      url='https://dsal.uchicago.edu/cgi-bin/app/steingass_query.py?page=XXXX')
    mydata = ET.tostring(data, encoding='unicode', method='xml')
    with open(f"{filename}.xml", "wt", encoding='utf-8') as f:
        f.write(mydata)
    tree = ET.parse(f'{filename}.xml')
    root = tree.getroot()
    pbar = tqdm(total=len(os.listdir('html_steingass')))
    for f_ in os.listdir('html_steingass'):
        list_ = get_items_local_steingass(f'html_steingass/{f_}')
        for it_word in list_:
            words_counter += 1
            element = root.makeelement('word', {})
            element2 = element.makeelement('pers', {})
            element2.set('original', it_word['word'].strip())
            element2.set('pronounce', it_word['pronounce'].strip())
            element2.set('dictionary', 'steingass')
            page_ = f_.split('.')[0].split('=')[-1]
            element2.set('page', page_)
            element3 = element.makeelement('eng', {})
            element3.set('translate1', it_word['text'].strip())
            element.append(element2)
            element.append(element3)
            root.append(element)
        pbar.update(1)
    pbar.close()
    tree.write(f'{filename}.xml', encoding='utf-8')
    print("Выполнено за : %s сек. Всего %s слов" %
          (time.time() - start_time, words_counter))


def second_iter_wth_deviant_xml(filename):
    # считываем файл с 'ошибками'
    tree = ET.parse(f'{filename}.xml')
    root = tree.getroot()
    # формируем файл, в котором нет переводов
    filename_wthout_trans = f"{filename}_deviant_withot_translatings.xml"
    data = ET.Element('xml', language='persian', note='without_translates',
                      url='https://dsal.uchicago.edu/cgi-bin/app/hayyim_query.py?page=XXXX')
    mydata = ET.tostring(data, encoding='unicode', method='xml')
    with open(filename_wthout_trans, "wt", encoding='utf-8') as f:
        f.write(mydata)
    tree_without_transls = ET.parse(filename_wthout_trans)
    root_without_transls = tree_without_transls.getroot()
    # остальные случаи
    filename_other = f"{filename}_deviant_other.xml"
    data = ET.Element('xml', language='persian', note='others',
                      url='https://dsal.uchicago.edu/cgi-bin/app/hayyim_query.py?page=XXXX')
    mydata = ET.tostring(data, encoding='unicode', method='xml')
    with open(filename_other, "wt", encoding='utf-8') as f:
        f.write(mydata)
    tree_others = ET.parse(filename_other)
    root_others = tree_others.getroot()
    counter1, counter2 = 0, 0
    pbar = tqdm(total=len(root))
    for elem in root:
        # print(elem[0].attrib)
        eng_translate = elem[1].attrib.get('translate1')
        if eng_translate == '':
            element = root_without_transls.makeelement('word', {})
            element1 = element.makeelement('pers', {})
            element1.set('original', elem[0].attrib.get('original'))
            element1.set('volume', elem[0].attrib.get('volume'))
            element1.set('page', elem[0].attrib.get('page'))
            element1.set('part_of_speech',
                         elem[0].attrib.get('part_of_speech'))
            element1.set('dictionary', 'hayyim')
            element2 = element.makeelement('eng', {})
            element2.set('translate1', eng_translate)
            element.append(element1)
            element.append(element2)
            root_without_transls.append(element)
            counter1 += 1
        else:
            element = root_others.makeelement('word', {})
            element1 = element.makeelement('pers', {})
            element1.set('original', elem[0].attrib.get('original'))
            element1.set('volume', elem[0].attrib.get('volume'))
            element1.set('page', elem[0].attrib.get('page'))
            element1.set('part_of_speech',
                         elem[0].attrib.get('part_of_speech'))
            element1.set('dictionary', 'hayyim')
            element2 = element.makeelement('eng', {})
            element2.set('translate1', eng_translate)
            element.append(element1)
            element.append(element2)
            root_others.append(element)
            counter2 += 1
        pbar.update(1)
    pbar.close()

    tree_without_transls.write(filename_wthout_trans, encoding='utf-8')
    tree_others.write(filename_other, encoding='utf-8')

    make_pretty_xml(filename_wthout_trans.split('.')[0])
    make_pretty_xml(filename_other.split('.')[0])
    print(f'Слов без переводов: {counter1}, с другими ошибками: {counter2}')


if __name__ == "__main__":
    # 1 словарь #
    print('\n\n\tИзвлечение слов из словаря "hayyim":')
    parse_dictionary_local_hayyim('hayyim_persian_local')
    second_iter_wth_deviant_xml('hayyim_persian_local_deviant')
    make_pretty_xml('hayyim_persian_local')
    make_pretty_xml('hayyim_persian_local_deviant')

    # 2 словарь #
    print('\n\tИзвлечение слов из словаря "steingass":')
    parse_dictionary_local_steingass('steingass_persian_local')
    make_pretty_xml('steingass_persian_local')

    print("\n\n\t\tThat's all!")
