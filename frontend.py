import redis
import uuid
import json

from flask import Flask, g, request, jsonify
from task import Task
from common.amqp_client import AmqpClient


app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    REDIS_HOST="localhost",
    REDIS_PORT=6379,
    REDIS_DB=0,
    DEBUG=True,
    AMQP_ADDRESS="amqp://guest:guest@localhost:5672//",
    AMQP_EXCHANGE="worker",
    AMQP_QUEUE="worker",
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
print app.config


def get_redis():
    """
    Init Redis
    """
    if not hasattr(g, 'redis_db'):
        g.redis_db = redis.StrictRedis(host=app.config['REDIS_HOST'], 
            port=int(app.config['REDIS_PORT']), db=int(app.config['REDIS_DB']))
    return g.redis_db


def get_rabbit():
    """
    Init Rabbit
    """
    if not hasattr(g, "rabbit"):
        queues = {
            app.config['AMQP_QUEUE']: {
                "routing_key": app.config['AMQP_QUEUE'],
                "exchange": app.config['AMQP_EXCHANGE']
            },
        }

        g.rabbit = AmqpClient(app.config['AMQP_ADDRESS'], 0, queues, {})
    return g.rabbit


# Read more about flask.jsonify here:
# http://flask.pocoo.org/docs/0.10/api/#module-flask.json
#
# It is also better to read the whole doc to get info about
# all flask functions

@app.route('/task', methods=['PUT'])
def create_task():
    """
    Add task to redis
    """

    json_data = request.json

    if not json_data:
        return "Not acceptable", 406

    if not isinstance(json_data, dict):
        return "Bad Request", 400

    r = get_redis()
    task = Task(uuid.uuid4().hex, json_data["type"])
    response = jsonify(id=task.id, 
        type=task.type, time_start=task.time_start,
        time_end=task.time_end)
    # TO print all variables of a class
    # print vars(response)
    r.set(task.id, response.response[0])

    get_rabbit().push_to_exchange(task.id, app.config['AMQP_EXCHANGE'], app.config['AMQP_QUEUE'])

    return response


@app.route('/task/<id>', methods=['GET'])
def get_task(id):
    """
    Get task from Redis
    """   
    r = get_redis()
    redis_data = r.get(id)
    if redis_data:
        data = json.loads(redis_data)
    else:
        return "Not found", 404

    task = Task(**data)
    return jsonify(id=task.id, 
        type=task.type, time_start=task.time_start,
        time_end=task.time_end, execute_time=task.execute_time)


if __name__ == "__main__":
    app.run(host="0.0.0.0")

