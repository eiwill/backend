import json
import logging
import os

from functools import wraps
from kombu import BrokerConnection, Exchange, Queue


def reconnect(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.connected():
            self.connect()

        return func(self, *args, **kwargs)

    return wrapper


class AmqpClient(object):

    def __init__(self, amqp_address, prefetch_count=10, queues={}, exchanges={}):
        self.amqp_address = amqp_address
        self.prefetch_count = prefetch_count

        self.connection = None
        self.channel = None

        self.queues = queues
        self.exchanges = exchanges

        self.declared_queues = {}
        self.declared_exchanges = {}
        self.consume = False

    def create_connection(self):
        return BrokerConnection(self.amqp_address)

    def connect(self):
        if not self.connection:
            logging.info("Connecting to server %s", self.amqp_address)
            self.connection = self.create_connection()
        else:
            return

        self.channel = self.connection.channel()
        self.channel.basic_qos(0, self.prefetch_count, False)

        for qname, params in self.queues.iteritems():
            if "exchange" in params:
                exchange = Exchange(params["exchange"], **self.exchanges.get(params["exchange"], {}))
                exchange = exchange(self.channel)
                exchange.declare()
                self.declared_exchanges[params["exchange"]] = exchange

                queue_params = params.copy()
                del queue_params['exchange']
                self.declared_queues[qname] = Queue(qname, exchange=exchange, **queue_params)
            else:
                self.declared_queues[qname] = Queue(qname, **params)

            self.declared_queues[qname](self.channel).declare()

    @reconnect
    def publish(self, message, queue):
        with self.connection.Producer(routing_key=queue) as producer:
            producer.publish(message)

    @reconnect
    def push_to_exchange(self, message, exchange, routing_key):
        ex = self.declared_exchanges.get(exchange)
        if not ex:
            return

        ex.publish(ex.Message(message), routing_key)

    @reconnect
    def subscribe(self, callback, queue):
        if not queue in self.declared_queues:
            return

        with self.connection.Consumer(self.declared_queues[queue], callbacks=[callback]) as consumer:
            self.consume = True
            while self.consume:
                self.connection.drain_events()

    def unsubscribe(self):
        self.consume = False

    def disconnect(self):
        if self.connection:
            self.connection.release()

    def connected(self):
        if self.connection:
            self.connection.ensure_connection()
        return self.connection
