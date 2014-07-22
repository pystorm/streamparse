(ns pixelcount
  (:use [backtype.storm.clojure])
  (:import [storm.kafka SpoutConfig
                        KafkaSpout
                        StringScheme]
           [com.google.common.collect.ImmutableList]
           [backtype.storm.spout.SchemeAsMultiScheme])
  (:gen-class))


(def kafka-config
  (SpoutConfig. (. ImmutableList of "kafkahost1" "kafkahost2")
                "pixels"
                "/storm_kafka"
                "pixel_reader"))
(set! (.scheme kafka-config) (SchemeAsMultiScheme. (StringScheme.)))
(def kafka-spout (KafkaSpout. kafka-config))


(def pixelcount
   [
    ;; spout configuration
    {"pixel-spout" (spout-spec kafka-spout)}

    ;; bolt configuration
    {"count-bolt" (shell-bolt-spec
           {"count-bolt" :shuffle}
           ["python" "pixelcount.py"]
           ["hour" "count"]
           :p 2
           )
    }
  ]
)
