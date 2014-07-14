(ns streamparse.word-count
  (:import [backtype.storm StormSubmitter LocalCluster])
  (:use [backtype.storm clojure config])
  (:gen-class))


(defn make-topology []
  (topology
    ;; spout configuration
    {"sentences" (shell-spout-spec
        ;; call streamparse sentence_spout.py (sentence_spout.py included in multilang/resources/sentence_spout.py)
        "python" "sentence_spout.py"
        ;; output fields
        ["sentence"]
        ;; parallelism hint
        :p 1)}
    ;; bolt configuration
    {"words" (shell-bolt-spec
        ;; indicates bolt uses a grouping of tuples from stream 1 on field "word"
        {"sentences" :shuffle}
        ;; call streamparse word_count (word_count.py included in multilang/resources/word_count.py)
        "python" "sentence_splitter.py"
        ;; output fields
        ["word"])
     "3" (shell-bolt-spec
        ;; field grouping on word
        {"words" ["word"]}
        ;; script
        "python" "word_count.py"
        ;; output fields
        [])
    }))

(defn run-local! []
  (let [cluster (LocalCluster.)]
    (.submitTopology cluster "word-count" {TOPOLOGY-DEBUG true} (make-topology))
    (Thread/sleep 10000)
    (.shutdown cluster)
    ))


(defn submit-topology! [name]
  (StormSubmitter/submitTopology
   name
   {TOPOLOGY-DEBUG true
    TOPOLOGY-WORKERS 3}
   (make-topology)))


(defn -main
  ([]
   (run-local!))
  ([name]
   (submit-topology! name)))
