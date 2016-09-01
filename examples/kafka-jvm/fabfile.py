import random
import time

import simplejson as json
from fabric.api import puts, task
from kafka.common import UnknownTopicOrPartitionError
from kafka.client import KafkaClient
from kafka.producer import SimpleProducer
from six.moves import range


def retry(tries, delay=3, backoff=2, safe_exc_types=None):
    """Retry a function call."""
    if safe_exc_types is None:
        # By default, all exception types are "safe" and retried
        safe_exc_types = (Exception,)

    def decorator(func):
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay

            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if not isinstance(e, safe_exc_types):
                        raise e


                    mtries -= 1
                    time.sleep(mdelay)
                    mdelay *= backoff
        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


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
def seed_kafka(kafka_hosts="streamparse-box:9092", topic_name="pixels",
               num_pixels=100000):
    """Seed the local Kafka cluster's "pixels" topic with sample pixel data."""
    kafka = KafkaClient(kafka_hosts)
    producer = SimpleProducer(kafka)
    # producer = SimpleProducer(kafka, batch_send=True, batch_send_every_n=1000,
    #                           batch_send_every_t=5)

    puts("Seeding Kafka ({}) topic '{}' with {:,} fake pixels..."
         .format(kafka_hosts, topic_name, num_pixels))
    pixels = random_pixel_generator()
    for i in range(num_pixels):
        pixel = json.dumps(next(pixels)).encode("utf-8", "ignore")
        try:
            producer.send_messages(topic_name, pixel)
        except UnknownTopicOrPartitionError:
            puts('Topic did not exist yet, so sleeping and trying again...',
                 flush=True)
            time.sleep(3)
        puts(i, end='\r', flush=True)
