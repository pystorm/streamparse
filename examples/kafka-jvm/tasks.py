import json
import random
import time
import logging

from invoke import task, run
from kafka.client import KafkaClient
from kafka.producer import SimpleProducer
from streamparse.ext.invoke import *


logging.basicConfig(format='%(asctime)-15s %(module)s %(name)s %(message)s')

def random_pixel_generator():
    urls = (
        "http://example.com/",
        "http://example.com/article1",
        "http://example.com/article2",
        "http://example.com/article3")
    while True:
        ip = "192.168.0.{}".format(random.randint(0, 255))
        url = random.choice(urls)
        ts = int(time.time() + random.randint(0, 30))
        yield {
            "ip": ip,
            "url": url,
            "ts": ts,
        }

@task
def seed_kafka(kafka_hosts=None, topic_name=None, num_pixels=100000):
    """Seed the local Kafka cluster's "pixels" topic with sample pixel data."""
    topic_name = topic_name or "pixels"
    kafka_hosts = kafka_hosts or "streamparse-box:9092"

    kafka = KafkaClient(kafka_hosts)
    producer = SimpleProducer(kafka)
    # producer = SimpleProducer(kafka, batch_send=True, batch_send_every_n=1000,
    #                           batch_send_every_t=5)

    print ("Seeding Kafka ({}) topic '{}' with {:,} fake pixels."
           .format(kafka_hosts, topic_name, num_pixels))
    pixels = random_pixel_generator()
    for i in xrange(num_pixels):
        pixel = json.dumps(pixels.next())
        producer.send_messages(topic_name, pixel)
    print "Done."

