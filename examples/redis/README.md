# streamparse + redis, simple example

This is a little derivation of the bundled `wordcount` project produced by
`sparse quickstart`.

In this version, there are two Python files that demonstrate how Spouts and
Bolts can be stored together inside Python modules easily thanks to the
streamparse runner. There is also no need for the `if __name__ == "__main__"`
boilerplate.

It also shows a simple in-memory WordCount bolt, and then a similar bolt, but
with word counting happening in-memory via a shared Redis instance.

This also is a simple demonstration of different data partitioning approaches.
In the `wordcount_mem` module, we need to partition the data such that every
word is bound to the same bolt instance. But in the case of `wordcount_redis`,
we can use a shuffle grouping between the Spout and Bolt since the words are
simply written to a single database, Redis.

Two small Python tools are also included in `tools/` that help monitor
processes running during `sparse run` invocations and help monitor the current
state of counters in your redis instance.

It's usually nice to run these tools in e.g. a tmux pane, so run `./watch.sh`
and `./top.sh` while playing with streamparse topology runs.

This example assumes you have redis installed locally (can run `redis-server`)
and that it's listening at localhost on the default port.
