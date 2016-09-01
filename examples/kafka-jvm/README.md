# kafka-jvm

This example demonstrates a topology which mixes JVM and Python components. In
this case, the topology will read pixels from the `pixels` Kafka topic which
are presumably collected from a web analytics or ad serving application. The
Kafka spout is JVM-based and defined in `src/clj/pixelcount/spouts/pixel_spout.clj`.

The tuples emitted by this spout are JSON-formatted strings and so a Python
bolt handles deserializing the JSON. Technically, this isn't needed as the
Kafka spout is entirely capable of performing this deserialization itself using
a custom Scheme instead of the current `StringScheme`. Implementing this is left
as an exercise for the reader.

Pixles are counted by URL in `pixel_count.PixelCounterBolt`.


# Instructions

### 1. Install Vagrant and Virtualbox
Install [Vagrant](https://www.vagrantup.com/) and [Virtualbox](https://www.virtualbox.org/).

### 2. Create Virtual Machine
Run `vagrant up` to create a virtual machine and use chef-solo to automatically provision it with:

- Java (openjdk 7)
- Python (2.7.5)
- pip (latest)
- virtualenv (latest)
- supervisord (latest)
- Apache Zookeeper
- Apache Storm (0.9.4)
- Kafka (0.8.1.1)

This will take a few minutes to fully provision the server. Once provisioned,
this server will have the following services accessible at `192.168.50.50`:

- Zookeeper: 2181
- Storm UI: 8080
- Storm Nimbus (Thrift): 6627
- Storm DRPC: 3772
- Storm DRPC Invocations: 3773
- Storm Logviewer: 8000
- Kafka: 9092

### 3. Modify /etc/hosts

In order to ensure that the settings within the VM work for both the
`sparse run` and `sparse submit` commands, you'll need to modify your
`/etc/hosts` file and add the following line:

```
192.168.50.50 streamparse-box
```

### 4. Setup ssh config

In order to `sparse submit` topologies to the Storm cluster running in your
virtual machine, streamparse requires ssh access to the box. Unfortunately,
vagrant uses some clever tricks when it executes `vagrant ssh` that we need to
copy. In order to allow streamparse to ssh into the box, we need to modify your
ssh config. Note that if you only wish to run this example via `sparse run`,
this step isn't necessary.

Run this command to append the necessary info to your local `~/.ssh/config`.

```
echo >> ~/.ssh/config && vagrant ssh-config | sed -e 's/Host default/Host streamparse-box/' -e 's/HostName 127.0.0.1/HostName 192.168.50.50/' -e 's/Port 2222/Port 22/' -e 's/LogLevel FATAL/LogLevel INFO/' >> ~/.ssh/config
```

You can confirm that ssh is configured properly by running `ssh streamparse-box`
which should allow you to ssh into your new virtual machine without Vagrant.

### 5. Seed the Kafka "pixels" topic

First, install necessary requirements via `pip install -r requirements.txt`
(preferrably inside a virtualenv).

Next, seed the `pixels` topic in Kafka with some sample data by running the
following command from outside of your VM:

```bash
fab seed_kafka
```

By default, this will seed the topic with 100,000 randomized pixels. Pixels are
JSON-formatted strings that look something like this:

```python
'{"ip": "192.168.1.122", "url": "http://example.com/", "ts": 1409253061}'
```

Oddly, you may have to run this command twice, once to create the topic, then
again to seed it. When the command is working properly, you'll see a message
like this:

```
Seeding Kafka (streamparse-box:9092) topic 'pixels' with 100,000 fake pixels.
Done.
```

### 6. Test the topology locally

Test the topology locally with:

```bash
sparse run --debug -t 15
```

It's helpful just to see the end result of this topology, so you can filter
the debug output to only those tuples emitted from the final bolt:

```bash
sparse run --debug -t 60 | grep "Emitting: pixel-count-bolt default"
```

If everything worked properly, you should soon see messages like:

```
31098 [Thread-27] INFO  backtype.storm.daemon.task - Emitting: pixel-count-bolt default ["http:\/\/example.com\/article3",26]
31241 [Thread-27] INFO  backtype.storm.daemon.task - Emitting: pixel-count-bolt default ["http:\/\/example.com\/article2",24]
31454 [Thread-27] INFO  backtype.storm.daemon.task - Emitting: pixel-count-bolt default ["http:\/\/example.com\/article1",32]
31703 [Thread-27] INFO  backtype.storm.daemon.task - Emitting: pixel-count-bolt default ["http:\/\/example.com\/",26]
```

### 7. Test submitting the topology

Seeing as your VM also has a Storm cluster, you can submit the topology to the
Storm cluster using `sparse submit`. Navigate to the
[Storm UI](http://streamparse-box:8080/index.html) to check out it's progress!
