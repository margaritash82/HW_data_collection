import json
import requests

# определяем категории (страница сайта с акциями обращается к странице с категориями, её парсим первой
params = {
    "records_per_page": 100,
    "page": 1,
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
}
url = "	https://5ka.ru/api/v2/categories/"

response: requests.Response = requests.get(url, params=params, headers=headers)
data = response.json()

for element in data:
    el_code = int(element.setdefault("parent_group_code", None))
    el_name = element.setdefault("parent_group_name",None)

    # определяем товары конкретной категории, которые стоят в акции (в параметры для парсинга добавляем код категории)
    params2 = {
        "records_per_page": 100,
        "categories": el_code,
        "page": 1,
    }

    url2 = "https://5ka.ru/api/v2/special_offers/"

    response2: requests.Response = requests.get(url2, params=params2, headers=headers)
    data2 = response2.json()
    products = []
    for product in data2:
        el_products = data2.get('results')
        products.append(el_products)

    category = {"name": el_name, "code": el_code, "products": products}
    with open(f'{el_code}.json', "w", encoding="UTF-8") as file:
        json.dump(category, file, ensure_ascii=False)
