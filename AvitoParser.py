import requests
from hyper.contrib import HTTP20Adapter
from bs4 import BeautifulSoup as bs4
from selenium import webdriver


class AvitoParser:
    def __init__(self):
        self.urls = [
            {
                'id': 'profnastil_nekonditsiya_tsena_za_metr_kvadratnyy_2394988828',
                'search_page': 'https://www.avito.ru/tambov/remont_i_stroitelstvo/stroymaterialy/vorota_zabory_i_ograzhdeniya-ASgBAgICAkRYoAKmvg3E5JkC?cd=1&q=профлист',
                'parse_time': '13:00'
            }
        ]
        self.headers = {
            'User-Agent': 'Magic User-Agent v999.26 Windows PRO 11',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
            'host': 'www.avito.ru'
        }
        self.driver = webdriver.Chrome()

    def process_urls(self, urls, session):
        if len(urls) <= 0:
            print('Ошибка количества объявлений!')
            return False

        for url in urls:
            url_data = self.find_ad(url, session)
            if url_data:
                print(url_data)
            else:
                print('Ошибка: данные о товаре пусты!')

    def find_ad(self, url, session):
        """ Поиск данных по конкретному объявлению """

        host = 'https://www.avito.ru'
        ad_url = url['search_page'][:8] + '/'.join(url['search_page'][8:].split('/')[:3]) + '/' + url['id']
        print(ad_url)

        # Вход на страницу объявления
        # res = session.get(ad_url, headers=self.headers)
        # if res.ok:
        # soup = bs4(res.text, 'html.parser')
        # ad_name = soup.find('span', class_='title-info-title-text').text
        # ad_name_q = ad_name.replace(' ', '+') if ' ' in ad_name else ad_name
        ad_selector = '.iva-item-titleStep-pdebR a'
        seller_selector = '.style-link-STE_U'
        # результирующий объект
        result = {
            'url': ad_url,
            'search': url['search_page'],
            'time': url['parse_time'],
            'position': '',
        }


        # Поиск на странице выдачи объявлений
        find_url = url['search_page']  # '/'.join([host, ad_region, ad_category]) + '?q=' + ad_name_q
        print('find:')
        print(find_url)
        # headers = self.headers
        ad_response = session.get(find_url, headers=self.headers)
            # self.driver.get(find_url)
        ad_response.encoding = 'utf-8'
        if ad_response.ok:
            with open('html.html', 'w', encoding='utf-8') as file:
                file.write(ad_response.text)
            search_html = bs4(ad_response.text, 'html.parser')
            ad_links = search_html.select(ad_selector)
            if len(ad_links) <= 0:  # Объявлений не найдено
                print('Количество ссылок: 0')
            else:
                ad_found = False
                link_id = 1
                for link in ad_links:
                    print(link.text)
                    # проверка на совпадение ссылки объявления с ссылкой в выборке
                    if url['id'] in link.get('href'):
                        ad_found = True
                        result['position'] = link_id
                        break
                    link_id += 1
                print("linkid:'",link_id)

                if not ad_found:  # Если не найдено объявлений, идёт поик по продавцам
                    seller_links = search_html.select(seller_selector)
                    result['position'] = []
                    if len(seller_links) <= 0:  # Пользователей нет
                        print('Ошибка: нет пользователей')
                    else:
                        for link in seller_links:
                            if url['id'] in seller_links:
                                result['position'] += link_id
                            link_id += 1
                    result['position'] = ','.join(result['position'])
            return result
        else:
            print('Ad response:', ad_response.status_code)
            return None
        # else:
        #     print('not ok', res.status_code)
        #     return None

    def process_data(self):
        """ Результирующий метод класса, использующий весь созданный функционал """

        # Открытие сессии
        s = requests.Session()
        s.mount('https://', HTTP20Adapter())
        self.process_urls(self.urls, s)
