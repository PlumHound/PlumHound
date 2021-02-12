import flask
from .phBackend import results

bp = flask.Blueprint('api', __name__)


@bp.route('/tasks')
def api():
    return flask.jsonify(results)
