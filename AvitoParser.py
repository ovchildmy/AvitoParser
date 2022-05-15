import json
import os.path
import datetime
import time

import pandas
from bs4 import BeautifulSoup as bs4
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


class AvitoParser:
    def __init__(self):
        self.urls = [
            {
                'id': 'i62128425',
                'search_page': 'https://www.avito.ru/tambov/remont_i_stroitelstvo/stroymaterialy/vorota_zabory_i_ograzhdeniya-ASgBAgICAkRYoAKmvg3E5JkC?cd=1&q=профлист',
                'parse_time': '13:00'
            },
            {
                'id': 'proflist_byudzhetnyy_na_dachu_2411599697',
                'search_page': 'https://www.avito.ru/tambov/remont_i_stroitelstvo/stroymaterialy/listovye_materialy-ASgBAgICAkRYoAKmvg2UxDU?cd=1&q=%D0%BF%D1%80%D0%BE%D1%84%D0%BB%D0%B8%D1%81%D1%82',
                'parse_time': '13:00'
            },
            {
                'id': '228acdc1ca9bed6fd9ed4ebd6c9ec74f',
                'search_page': 'https://www.avito.ru/moskva/avtomobili/ford-ASgBAgICAUTgtg2cmCg?q=форд+новый&radius=75',
                'parse_time': '13:00'
            },
        ]
        self.headers = {
            'User-Agent': 'Magic User-Agent v999.26 Windows PRO 11',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
            'host': 'www.avito.ru'
        }

    def process_urls(self, urls):
        if len(urls) <= 0:
            print('Ошибка количества объявлений!')
            return False

        for url in urls:  # Обработка каждого объявления/продавца
            url_data = self.find_ad(url)
            if url_data:
                if os.path.exists('data.json'):  # Если данные уже существуют
                    with open('data.json', 'r', encoding='utf-8') as file:
                        data = json.load(file)
                    if len(data) > 0:
                        item_found = False
                        for item in data:
                            if item['url'] == url_data['url']:  # Если id объявления/продавца совпадают
                                item_found = True
                                print('совпадение, добавим!')
                                item['pos_data'].insert(0, url_data['pos_data'][0])
                                if len(item['pos_data']) > 5:  # Если накопилось больше пяти объявлений
                                    del item['pos_data'][5:]
                                break

                        if not item_found:
                            data.append(url_data)

                        with open('data.json', 'w', encoding='utf-8') as file:
                            print('write:', data)
                            json.dump(data, file, ensure_ascii=False, indent=4)
                else:
                    with open('data.json', 'w', encoding='utf-8') as file:
                        data = [url_data]
                        print('write:', data)
                        json.dump(data, file, ensure_ascii=False, indent=4)
            else:
                print('Ошибка: данные о товаре пусты!')

    def find_ad(self, url):
        """ Поиск данных по конкретному объявлению """

        host = 'https://www.avito.ru'
        # ad_url = url['search_page'][:8] + '/'.join(url['search_page'][8:].split('/')[:3]) + '/' + url['id']
        ad_selector = '.iva-item-titleStep-pdebR a'
        seller_selector = '.iva-item-aside-GOesg'
        date = str(datetime.datetime.now().date().day) + '.' + str(datetime.datetime.now().date().month)
        # результирующий объект
        result = {
            'url': '-',
            'search': url['search_page'],
            'time': url['parse_time'],
            'pos_data': [{
                'position': '',
                'date': date,
            }]
        }

        # Поиск на странице выдачи объявлений
        find_url = url['search_page']

        self.driver.get(find_url)
        search_html = bs4(self.driver.page_source, 'html.parser')
        ad_links = search_html.select(ad_selector)
        if len(ad_links) <= 0:  # Объявлений не найдено
            print('Количество ссылок: 0')
        else:
            ad_found = False
            link_id = 1
            for link in ad_links:
                # проверка на совпадение ссылки объявления с ссылкой в выборке
                if url['id'] in link.get('href'):
                    ad_found = True
                    result['url'] = host + link.get('href')
                    result['pos_data'][0]['position'] = link_id
                    break
                link_id += 1

            if not ad_found:  # Если не найдено объявлений, идёт поик по продавцам
                seller_links = search_html.select(seller_selector)
                result['pos_data'][0]['position'] = []
                if len(seller_links) <= 0:  # Пользователей нет
                    print('Ошибка: нет пользователей')
                    return None
                else:
                    link_id = 1
                    for link in seller_links:
                        needle = url['id']
                        if needle in link.decode_contents():
                            for author_link in link.findAll('a'):
                                if needle in author_link.get('href'):
                                    result['url'] = host + author_link.get('href')
                            result['pos_data'][0]['position'].append(str(link_id))
                        link_id += 1
                result['pos_data'][0]['position'] = ','.join(result['pos_data'][0]['position'])
        return result
    
    def save_to_excel(self):
        # Взятие готовой информации из файла
        with open('data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Подготовка датафрейма
        now = datetime.datetime.now()
        date_list = []
        for i in range(5):
            date_list.append((now-datetime.timedelta(days=i)).strftime('%#d.%#m'))
        pd_data = []
        indexes = ['Время парсинга', 'Страница поиска', 'ID объявления/продавца', 'Ключевое слово', 'Город']
        for date in date_list:
            indexes.append(date)
        for item in data:
            item_split = item['search'].split('/')
            item_city = item_split[3]
            item_keyword = item_split[-1].split('q=')[-1].split('&')[0].replace('+', ' ') if 'q=' in item_split[-1] \
                else ''
            item_ar = [item['time'], item['search'], item['url'], item_keyword, item_city]
            # Обработка позиций по датам
            for date in date_list:
                found_date = False
                for pos_item in item['pos_data']:
                    if pos_item['date'] == date:
                        item_ar.append(pos_item['position'])
                        found_date = True
                        break
                if not found_date:
                    item_ar.append('')
            pd_data.append(item_ar)
        print('write to db:', data)
        df = pandas.DataFrame(pd_data, columns=indexes)
        df.to_excel('avito_parse.xlsx', columns=indexes)

    def get_ads_data(self):
        """ Получение объявлений и продавцов для обработки """
        file_name = 'find.txt'
        delim = '-----'
        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8') as f:
                file = f.read()
                ads = file.split(delim)[1].split('\n\n')
                result = []
                # print(ads)
                for ad in ads:
                    ad = list(filter(None, ad.split('\n')))
                    parse_time = ad[2]
                    if parse_time == datetime.datetime.now().strftime('%H:%M'):
                        result.append({
                            'id': ad[0],
                            'search_page': ad[1],
                            'parse_time': parse_time,
                        })
                    else:
                        print('Позиция не проходит по времени!')
                if len(result) == 0:
                    return None
                print('Данные присутствуют! Начинается обработка', result)
                return result
        else:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write('Шаблон:\nID Объявления/продавца\nСтраница поиска\nВремя обработки\n'
                        '(перед сделующим объектом пропустить строку)\n' + delim)
            print('Введите данные в файл', file_name)
            return None

    def process_data(self):
        """ Результирующий метод класса, использующий весь созданный функционал """
        while True:
            ads_data = self.get_ads_data()
            if ads_data:
                options = Options()
                options.add_argument("--headless")
                self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
                self.process_urls(ads_data)
                self.driver.quit()
                self.save_to_excel()
            time.sleep(60)
