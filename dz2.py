import os
from dotenv import load_dotenv
import requests
from urllib.parse import urljoin
import bs4
import pymongo
import datetime
import time

class ParseError(Exception):
    def __init__(self, txt):
        self.txt = txt

class MagnitParser:
    def __init__(self, start_url, data_base):
        self.start_url = start_url
        self.database = data_base["gb_parse_20_01_2021"]



    @staticmethod
    def __get_response(url, *args, **kwargs):
        while True:
            try:
                response = requests.get(url, *args, **kwargs)
                if response.status_code > 399:
                    raise ParseError(response.status_code)
                time.sleep(0.1)
                return response
            except (requests.RequestException, ParseError):
                time.sleep(0.5)
                continue

    @property
    def data_template(self):
        return {
            "url": lambda tag: urljoin(self.start_url, tag.attrs.get("href")),
            "promo_name": lambda tag: tag.find(
                'div', attrs={"class": "card-sale__header"}
            ).text,
            "product_name": lambda tag: tag.find(
                "div", attrs={"class": "card-sale__title"}
            ).text,
            "old_price": lambda tag: float(
                '.'.join(list((tag.find(
                "div", attrs={"class": "label__price_old"}
            ).text).split()))),
            "new_price": lambda tag: float(
                '.'.join(list((tag.find(
                    "div", attrs={"class": "label__price_new"}
                ).text).split()))),
            "image_url": lambda tag: urljoin(self.start_url, tag.find("source").attrs.get("data-srcset")),
            "data_from": lambda tag: self.data_from(list((tag.find(
                   "div", attrs={"card-sale__date"}
            ).text).split())),
            "data_to": lambda tag: self.data_to(list((tag.find(
                "div", attrs={"card-sale__date"}
            ).text).split())),
        }

    @staticmethod
    def data_from(adress):
        datalist = ['нет данных', 'января', 'февраля', 'марта', 'апреля',
                    'мая', 'июня', 'июля', 'августа', 'сентября',
                    'октября', 'ноября', 'декабря']

        new_adress = []
        for el in adress:
            if el in datalist:
                i = datalist.index(el)
                new_adress.append(i)
            else: new_adress.append(el)
        new_adress = new_adress[1:3]
        new_adress.append('2021')
        new_string = '.'.join(str(j) for j in new_adress)
        format = '%d.%m.%Y'
        data_from = datetime.datetime.strptime(new_string, format)
        return data_from

    @staticmethod
    def data_to(adress):
        datalist = ['нет данных', 'января', 'февраля', 'марта', 'апреля',
                    'мая', 'июня', 'июля', 'августа', 'сентября',
                    'октября', 'ноября', 'декабря']

        new_adress = []
        for el in adress:
            if el in datalist:
                i = datalist.index(el)
                new_adress.append(i)
            else:
                new_adress.append(el)
        new_adress = new_adress[4:6]
        new_adress.append('2021')
        new_string = '.'.join(str(j) for j in new_adress)
        format = '%d.%m.%Y'
        data_to = datetime.datetime.strptime(new_string, format)
        return data_to

    @staticmethod
    def __get_soup(response):
        return bs4.BeautifulSoup(response.text, "lxml")

    def run(self):
        for product in self.parse(self.start_url):
            self.save(product)

    def validate_product(self, product_data):
        return product_data

    def parse(self, url):
        soup = self.__get_soup(self.__get_response(url))
        catalog_main = soup.find("div", attrs={"class": "сatalogue__main"})
        for product_tag in catalog_main.find_all(
            "a", attrs={"class": "card-sale"}, reversive=False
        ):
            yield self.__get_product_data(product_tag)


    def __get_product_data(self, product_tag):
        data = {}
        for key, pattern in self.data_template.items():
            try:
                data[key] = pattern(product_tag)
            except (AttributeError, ValueError):
                continue
        return data

    def save(self, data):
        collection = self.database["magnit_1"]
        collection.insert_one(data)


if __name__ == "__main__":
    load_dotenv('.env')
    data_base = pymongo.MongoClient(os.getenv("DATA_BASE_URL"))

    parser = MagnitParser("https://magnit.ru/promo/?geo=moskva", data_base)
    parser.run()