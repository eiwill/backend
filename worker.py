import argparse
import anyconfig
import time
import json
import logging
import redis
import Queue

from common.amqp_client import AmqpClient
from task import Task
from threading import Thread, Event


def create_arg_parser():
    parser = argparse.ArgumentParser(description="Basic worker")
    parser.add_argument("-c", "--config-file", dest="config_file", help="Config File", default="conf.d/config.json")
    parser.add_argument("-a", "--amqp-address", dest="amqp_address", help="AMQP address")
    parser.add_argument("-th", "--worker-threads", dest="worker_threads", help="Worker threads")
    parser.add_argument("-rh", "--redis-host", dest="redis_host", help="Redis host")
    parser.add_argument("-rp", "--redis-port", dest="redis_port", help="Redis port")
    return parser


def load_config(options):
    conf = anyconfig.load(options.config_file, "json")
    for i, value in vars(options).iteritems():
        if value is not None and i in conf:
            conf[i] = value

    return conf


if __name__ == "__main__":
    arg_parser = create_arg_parser()
    options = arg_parser.parse_args()   # return object with args

    conf = load_config(options)

    amqp_client = AmqpClient(conf["amqp_address"], int(conf["worker_threads"]), conf["queues"])
    r = redis.StrictRedis(host=conf["redis_host"], port=int(conf["redis_port"]))

    processing_queue = Queue.Queue()
    processors = []
    stop_event = Event()

    def process(task):
        print "Processing %s" % task.id 
        time.sleep(2)
        task.time_end = time.time()
        r.set(task.id, json.dumps(dict(id=task.id, 
        type=task.type, time_start=task.time_start,
        time_end=task.time_end)))

    def handle_message(body, message):
        print body
        redis_data = r.get(body)
        if redis_data:
            data = json.loads(redis_data)
        else:
            logging.error("Failed to get task %s from Redis", body)

        task = Task(**data)
        processing_queue.put((task, message))

    def run():
        while not stop_event.is_set():
            try:
                task, message = processing_queue.get(timeout=0.5)
                process(task)
                processing_queue.task_done()
                message.ack()
            except Queue.Empty:
                continue   

    try:
        while len(processors) < int(conf["worker_threads"]):
            process_thread = Thread(target=run)
            process_thread.daemon = True
            process_thread.start()
            processors.append(process_thread)
        amqp_client.subscribe(handle_message, conf["input_queue"])
    except KeyboardInterrupt:
        logging.exception("Keyboard interrupt")
    finally:
        amqp_client.unsubscribe()
        stop_event.set()
        logging.info("Asking threads to stop")
        for thread in processors:
            thread.join()

        amqp_client.disconnect()
    

