### 1.1.0 - Jan 26, 2015

This release adds support for Storm 0.9.3 in addition to a number of bug fixes. 
New and updated examples available.

* Adds: [Support for Storm 0.9.3 heartbeats (#82)](https://github.com/Parsely/streamparse/issues/82)
* Adds: [`StormHandler` class for logging to Storm](https://github.com/Parsely/streamparse/pull/58)
* Adds: `--wait` timeout to `sparse kill` and `spare submit`
* Adds: "kafka-jvm" example -- mixed language topology (JVM/clojure + Python) with JVM-based Kafka Spout 
* Adds: "wordcount-on-redis" example
* Updates: wordcount example
* Fixes: [#64: `sparse tail fails when logs are missing](https://github.com/Parsely/streamparse/issues/64) 
* Fixes: ["flush" method to LogStream](https://github.com/Parsely/streamparse/pull/50)
* Fixes: [#100: SSH tunnels are not always closed](https://github.com/Parsely/streamparse/issues/100) 
* Fixes: -o option string issues
* Documentation updates


### 1.0.1 - Aug 28, 2014

Fixes bug in #57 regarding executing local tasks (like sparse run) with
pty=True.

### 1.0.0 - Aug 25, 2014

This is a major release that introduces several potentially breaking API
changes, hence the major version advancement to 1.0.0. Please read the changes
below as well as our [migration wiki](https://github.com/Parsely/streamparse/wiki/0.0.13-to-1.0.0-Migration-Guide)
guide before upgrading.


**streamparse runner**

* Added a new runner for topology components and as a result, a new way to
  define topologies (extension to the existing Clojure DSL). More info can be
  found in the docs and in the [1.0.0 migration guide](https://github.com/Parsely/streamparse/wiki/0.0.13-to-1.0.0-Migration-Guide).
* Quickstart projects have been updated to now have nested directories
  "src/bolts" and "src/spouts".


**Component API updates**

* Added `auto_anchor`, `auto_ack` and `auto_fail` flags to base Bolt class. See
  docs for detailed descriptions of these flags and migration page for info on
  how to safely upgrade your bolts.
* `BasicBolt` is now deprecated.
* Class var `BatchingBolt.SECS_BETWEEN_BATCHES` renamed to
  `secs_between_batches` since this isn't a constant, just a setting.
* `Spout.emit` and `Bolt.emit` now returns a list of task IDs a tuple was
  emitted to unless `need_task_ids` kwarg is set to `False`.
* `Spout.emit_many` and `Bolt.emit_many` now return a two-dimensional list of
  the task IDs each emit tuple was sent to unless `need_task_ids` kwarg is set
  to `False`.
* `BatchingBolt` does not return task IDs due to concurrency issues that will
  be addressed in a future release.
* Spouts and bolts now have the following instance variables which users are
  free to use. These are initialized before the call to  `initialize()`:
  * `_topology_name` - name of the topology when submitted to Storm.
  * `_task_id` - task ID of the current component in the topology.
  * `_component_name` - the name of the current component as defined in the
    Clojure definition (e.g. "my-bolt").
  * `_debug` - the `topology.debug` setting (configured using the sparse
    `--debug` flag).
  * `_storm_conf` - the entire config dict recieved on initial handshake.
  * `_context` - the entire context dict receieved on initial handshake.
* `BatchingBolt` threads (main and _batcher) now have more descriptive names.


**IPC**

* A lot of code cleanup around how we read from and write to stdin and stdout.
  Much more stable here but no breaking changes for users since they should
  never interface with these methods directly.


**Logging**

* Full support for Python logging has now been added. Lots of info in the docs
  on this and the migration guide.  Logging config settings added to new
  quickstart projects.
* print statements are now properly sent to the component's log file - feel
  free to add print statements for handy debugging or better yet, create a
  logger for nicely formatted messages.
* Full support for Storm log levels once STORM-414 is merged in.


**Administration**

* Added pre and post submit hooks in fabric and invoke for topologies to
  enable users to run  arbitrary code (e.g. send IRC message) after topologies
  are submitted (info in docs).\
* `sparse tail` command now requires `-n <topology>` argument as it will tail
  only the logs for a specific topology and environment.
* Added `remove_logs` fab task which users can optionally hook up to a
  `pre_submit` hook to clear out Python logs.


**Testing**

* Better test support added for all our components, more improvements to come
  here.


### 0.0.9 - June 11, 2014

This release includes changes to `sparse submit` and `sparse run` that allow you
to tune topology workers and ackers and their parallelism levels. There is also
a mechanism now to override any Storm topology option per-submit or per-run,
e.g. topology.message.timeout or topology.max.spout.pending.

### 0.0.8 - May 30, 2014

Cluster management fixes.

This release fixes an issue where sparse submit limited to 3 workers and always
submitted with "debug mode" by default. This would slowdown production clusters
needlessly.

### 0.0.7 - May 13, 2014

bugfix release

### 0.0.6 - May 12, 2014

- added `sparse submit` for topology building and sending to remote cluster
- added `sparse list` and `sparse kill` management commands
- added `sparse tail` for tailing logs on remote workers
- fix a bug in `streamparse.bolts`

### 0.0.5 - May 4, 2014

- initial release with `sparse quickstart` and `sparse run`

