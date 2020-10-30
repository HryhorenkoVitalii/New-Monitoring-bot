from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Tuple
from urllib.parse import urlparse
from langdetect import detect
from tqdm import tqdm
from datetime import datetime, timedelta
from requests import Session
from fake_useragent import UserAgent
from newspaper import Article


class UkrNetNews:
    _api_url_template: str = "https://www.ukr.net/news/dat/{category}/{page}/"

    def __init__(self, session: Session = None):
        self.session = session or Session()
        self.session.headers.update({
            "User-Agent": UserAgent().random
        })

    def _fetch_news_json(self, category: str, page: int = 1):
        api_url = self._api_url_template.format(category=category, page=page)
        json_response = self.session.get(api_url).json()
        news_records = json_response["tops"]
        news_data: List[dict] = list()

        for record in news_records:
            if "News" in record:
                news_data.extend(record["News"])
            elif 'Dups' in record:
                news_data.extend(record["Dups"])

            news_data.append(record)

        category_dict = {"politika": "politics", "jekonomika": "economy", "proisshestvija": "incidents",
                         "tehnologii": "technology", "avto": "auto", "zdorove": "health", "show_biznes": "showbiz"}

        for record in news_data:
            record["DateCreated"] = datetime.fromtimestamp(record["DateCreated"])
            record["Category"] = category
            record["Language"] = detect(record["Title"])
            for key in ["NewsId", "Id", "HasImage", "HasVideo", "Details", "NewsCount", "Transition",
                        "PartnerId", "SeoTitle", "TopValue", "DateLast", "News", "Dups", "OriginalId"]:
                if key in record:
                    del record[key]
            if record["Category"] in category_dict:
                record.update({"Category": category_dict[record["Category"]]})

        print(f"News before filtering: {len(news_data)}")
        filtered_news = list(filter(lambda news_item: urlparse(news_item["Url"]).scheme, news_data))
        print(f"News after filtering: {len(filtered_news)}")
        return filtered_news

    def _date_check(self, date_from, date_to=None):
        if date_to is None:
            date_out = datetime.now()
        else:
            if len(date_to) <= 10:
                date_out = datetime.strptime(date_to, "%Y-%m-%d")
            else:
                date_out = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S")
        if len(date_from) <= 10:
            date_in = datetime.strptime(date_from, "%Y-%m-%d")
        else:
            date_in = datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S")

        return date_in, date_out

    def date_filter(self, news_json, date_from: str, date_to=None):
        delta_time = self._date_check(date_from, date_to)
        result_list = []
        for news in news_json:
            if news["DateCreated"] >= delta_time[0] and news["DateCreated"] <= delta_time[1]:
                result_list.append(news)

        return (result_list)

    def last_news(self, minutes: int) -> List[dict]:
        category_dict = ["politika", "jekonomika", "proisshestvija", "society", "tehnologii", "science",
                         "avto", "sport", "zdorove", "show_biznes"]
        result = []
        time = datetime.now() - timedelta(minutes=minutes)
        for category in category_dict:
            page = 0
            while True:
                temp_list = []
                page += 1
                fetch_json = self._fetch_news_json(category=category, page=page)
                if fetch_json[-1]["DateCreated"] >= time:
                    for news in fetch_json:
                        temp_list.append(news)
                    continue
                else:
                    print(len(fetch_json))
                    for news in fetch_json:
                        temp_list.append(news)
                    for news in temp_list:
                        if news["DateCreated"] >= time:
                            result.append(news)
                break
        return result


def download_news_content(news: dict) -> Tuple[dict, bool]:
    is_parsed = False
    article = Article(news["Url"])
    try:
        article.download()
        article.parse()
        full_description = article.text
    except Exception as e:
        print(e)
        full_description = None

    if full_description:
        is_parsed = True
        news.update({"Content": full_description.replace("\n", " ")})

    return news, is_parsed


def news_content(news_json):
    with ThreadPoolExecutor() as pool:
        tasks = [pool.submit(download_news_content, news_item) for news_item in news_json]
        parsed_news = [task.result() for task in tqdm(tasks)]

    failed_news = list(filter(lambda item: not item[-1], parsed_news))
    print(f"Failed news: {len(failed_news)}")
    return parsed_news


def check_content(news_json):
    count_content = 0
    no_content_dict = []
    for news in news_json:
        if news[1] is True:
            pass
        else:
            count_content += 1
            no_content_dict.append(news[0])
    if count_content == len(news_json):
        print("Нема \"Content\" в одной з новин")
        return False
    elif count_content != 0:
        print("В деяких новинах не вистачае \"Content\"")
        return count_content, no_content_dict
    else:
        print("Всі новини з\"Content\"")
        return True

