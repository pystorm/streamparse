(ns wordcount
  (:use     [backtype.storm.clojure])
  (:gen-class))

(def wordcount
   [
    ;; spout configuration
    {"word-spout" (shell-spout-spec
          ["python" "words.py"]
          ["word"]
          )
    }
    ;; bolt configuration
    {"count-bolt" (shell-bolt-spec
           {"word-spout" :shuffle}
           ["python" "wordcount.py"]
           ["word" "count"]
           :p 2
           )
    }
  ]
)
