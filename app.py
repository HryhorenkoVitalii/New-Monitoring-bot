from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from utils import str_to_date_converter
from functools import wraps

news_bot_api = Flask("NewsBot")

news_bot_api.config['SQLALCHEMY_DATABASE_URI'] = db
db = SQLAlchemy(news_bot_api)
ma = Marshmallow(news_bot_api)

x_api_key = ["pasword"]

def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-api-key') and request.headers.get('X-api-key') in x_api_key:
            return view_function(*args, **kwargs)
        else:
            return {"Message": "Key is invalid"}, 403
    return decorated_function


class News(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    cluster_id = db.Column(db.Integer())
    date_created = db.Column(db.DateTime(), default=datetime.now())
    title = db.Column(db.String(length=240))
    description = db.Column(db.String())
    partner_title = db.Column(db.String())
    url = db.Column(db.String())
    category = db.Column(db.String())
    language = db.Column(db.String())
    content = db.Column(db.String(), nullable=True)

    def __init__(self, date_created, cluster_id: int, title: str,
                 description: str, partner_title: str, url: str, category: str,
                 language: str, content: str = None):
        self.cluster_id = cluster_id
        self.date_created = date_created
        self.title = title
        self.description = description
        self.partner_title = partner_title
        self.url = url
        self.category = category
        self.language = language
        self.content = content


class NewsSchema(ma.Schema):
    class Meta:
        fields = ("cluster_id", "date_created", "title", "description", "partner_title",
                  "url", "category", "language", "content")


news_schema = NewsSchema()
news_schemas = NewsSchema(many=True)

db_filters = {
    "cluster_id": News.cluster_id,
    "date_created": News.date_created,
    "title": News.title,
    "description": News.description,
    "partner_title": News.partner_title,
    "url": News.url,
    "category": News.category,
    "language": News.language,
    "content": News.content
}


@news_bot_api.route("/api/v1/news", methods=["GET", "POST"])
@require_appkey
def news(page=1):
    if request.method == 'GET':
        if request.args.get("page"):
            page = int(request.args.get("page"))
        if request.args.get("filter"):
            filter = request.args.get("filter").split(",")
            if filter[0] == "date_created":
                value = str_to_date_converter(filter[2])
            elif filter[0] == "cluster_id":
                value = int(filter[1])
            else:
                value = filter[2]
            if filter[1] == "=":
                news = News.query.filter(db_filters[filter[0]] == value).paginate(per_page=10, page=page, error_out=False)
            elif filter[1] == ">":
                news = News.query.filter(db_filters[filter[0]] > value).paginate(per_page=10, page=page, error_out=False)
            elif filter[1] == "<":
                news = News.query.filter(db_filters[filter[0]] < value).paginate(per_page=10, page=page, error_out=False)
        else:
            news = News.query.paginate(per_page=10, page=page, error_out=False)
        if page > news.pages:
            return {"Message": "Page not found"}, 404
        result = {"page": f"{page}/{news.pages}",
                  "news": news_schemas.dump(news.items)}
        return jsonify(result)
    elif request.method == 'POST':
        cluster_id = request.json["cluster_id"]
        date_created = request.json["date_created"]
        title = request.json["title"]
        description = request.json["description"]
        partner_title = request.json["partner_title"]
        url = request.json["url"]
        category = request.json["category"]
        language = request.json["language"]
        content = request.json["content"]

        data = str_to_date_converter(date_created)

        new_news = News(data, cluster_id, title, description, partner_title,
                        url, category, language, content)

        db.session.add(new_news)
        db.session.commit()

        return news_schema.jsonify(new_news)



@news_bot_api.route("/api/v1/news/<int:id>", methods=["GET", "PUT"])
@require_appkey
def news_details(id):
    news = News.query.get(id)
    if request.method == 'GET':
        result = news_schema.dump(news)
        return jsonify(result)
    elif request.method == 'PUT':
        cluster_id = request.json["cluster_id"]
        date_created = request.json["date_created"]
        title = request.json["title"]
        description = request.json["description"]
        partner_title = request.json["partner_title"]
        url = request.json["url"]
        category = request.json["category"]
        language = request.json["language"]
        content = request.json["content"]

        data = str_to_date_converter(date_created)

        news.data = data
        news.cluster_id = cluster_id
        news.title = title
        news.description = description
        news.partner_title = partner_title
        news.url = url
        news.category = category
        news.language = language
        news.content = content

        db.session.commit()

        return news_schema.jsonify(news)


if __name__ == "__main__":
    news_bot_api.run()
