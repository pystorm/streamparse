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

