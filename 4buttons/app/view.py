from app import app
import config
from flask import render_template


@app.route('/mobile_test', methods=["GET"])
def viewShow():
    return render_template("demo.html", namespace=config.NAMESPACE)


@app.route('/', methods=["GET"])
@app.route('/index', methods=["GET"])
def index():
    return render_template("index.html")


@app.route('/mobile', methods=["GET"])
def mobile():
    return render_template("mobile.html", namespace=config.NAMESPACE)


@app.route('/browser', methods=["GET"])
def browser():
    return render_template("browser.html", lists_for_matching = [config.LIST_FOR_ID, config.LIST_FOR_PASSPORTS])


@app.route('/video_stream', methods=["GET"])
def video_stream():
    return render_template("video-stream.html", namespace=config.NAMESPACE)


@app.route('/passport_stream', methods=["GET"])
def passport_stream():
    return render_template("passport-stream.html", namespace=config.NAMESPACE)


@app.route('/create_id', methods=["GET"])
def create_id():
    return render_template("create-id.html", list_id=config.LIST_FOR_ID)
