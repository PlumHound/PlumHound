import flask
import os


app = flask.Flask(__name__)


results = None


def start(port, res):
    global results
    results = res

    from .phApi import bp as api

    app.register_blueprint(api, url_prefix='/api')

    app.run(port=port)


build_folder = os.path.join('..', 'frontend', 'build')
static_folder = os.path.join(build_folder, 'static')


@app.route('/')
@app.route('/index.html')
def send_index():
    return flask.send_file(str(os.path.join(build_folder, 'index.html')))


@app.route('/asset-manifest.json')
def send_asset_manifest():
    return flask.send_file(str(os.path.join(build_folder, 'asset-manifest.json')))


@app.route('/static/<path:path>')
def send_static(path):
    return flask.send_from_directory(str(static_folder), path)



