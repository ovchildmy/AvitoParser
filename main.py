""" Скрипт по поиску позиций выбранных объявлений на Авито """

from AvitoParser import AvitoParser

if __name__ == '__main__':
    parser = AvitoParser()
    parser.process_data()