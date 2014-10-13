(ns wordcount-mem
  (:use     [streamparse.specs])
  (:gen-class))

(defn wordcount-mem [options]
   [
    ;; spout configuration
    {"word-spout" (python-spout-spec
          options
          "wordcount_mem.WordSpout"
          ["word"]
          )
    }
    ;; bolt configuration
    {"count-bolt" (python-bolt-spec
          options
          ;; field group on word due to memory storage
          {"word-spout" ["word"]}
          "wordcount_mem.WordCountBolt"
          ["word" "count"]
          :p 2
          )
    }
  ]
)
