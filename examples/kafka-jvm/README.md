A streamparse example which demonstrates using JVM and Python components in a
single topology.  In this case, the topology will read "pixels" from Kafka,
presumably collected for a web analytics or ad serving application, using a
JVM-based `KafkaSpout`.  It will then count pixels by hour using Python-based
bolts.