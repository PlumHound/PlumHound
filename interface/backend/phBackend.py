import flask
import os


app = flask.Flask(__name__, static_folder='../frontend/build/static')
app.debug = True
results = None

build_folder = os.path.join('..', 'frontend', 'build')


@app.route('/')
def send_index():
    return flask.send_from_directory(build_folder, 'index.html')


@app.route('/<path:path>')
def send_static(path):
    return flask.send_from_directory(build_folder, path)


def start(port, res):
    global results
    results = res

    from .phApi import bp as api

    app.register_blueprint(api, url_prefix='/api')

    app.run(port=port)
