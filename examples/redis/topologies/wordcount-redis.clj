(ns wordcount-redis
  (:use     [streamparse.specs])
  (:gen-class))

(defn wordcount-redis [options]
   [
    ;; spout configuration
    {"word-spout" (python-spout-spec
          options
          "wordcount_redis.WordSpout"
          ["word"]
          )
    }
    ;; bolt configuration
    {"count-bolt" (python-bolt-spec
          options
          ;; shuffle grouping since data sent to Redis
          {"word-spout" :shuffle}
          "wordcount_redis.WordCountBolt"
          ["word" "count"]
          :p 4
          )
    }
  ]
)
