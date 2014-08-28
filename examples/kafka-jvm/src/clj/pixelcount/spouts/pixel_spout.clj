(ns pixelcount.spouts.pixel_spout
  (:import [storm.kafka SpoutConfig KafkaSpout KafkaConfig KafkaConfig
                        StringScheme ZkHosts]
           [backtype.storm.spout SchemeAsMultiScheme]))


;; Config spelled out below here to get the reader more comfortable with
;; Clojure
;; ^{...} adds metadata to a var definition
(def ^{:doc "Host string for Zookeeper"}
  zk-hosts "streamparse-box:2181"
  )


;; Default path, shouldn't be a need to change this
(def ^{:doc "Zookeeper broker path"}
  zk-broker-path "/brokers")

(def kafka-zk-hosts (ZkHosts. zk-hosts zk-broker-path))

(def ^{:doc "Topic name"}
  topic-name "pixels")

(def ^{:doc "Root path of Zookeeper for spout to store consumer offsets"}
  kafka-zk-root "/kafka_storm")

(def ^{:doc "ID for this Kafka consumer"}
  kafka-consumer-id "pixel_reader")

(def ^{:doc "Kafka spout config definition"}
  spout-config (let [cfg (SpoutConfig. kafka-zk-hosts topic-name kafka-zk-root kafka-consumer-id)]
                  (set! (. cfg scheme) (SchemeAsMultiScheme. (StringScheme.)))
                  ;; During testing, it's usually valuable to force a spout to
                  ;; read from the beginning of a topic
                  (set! (. cfg forceFromStart) true)
                  cfg))

(def spout (KafkaSpout. spout-config))
