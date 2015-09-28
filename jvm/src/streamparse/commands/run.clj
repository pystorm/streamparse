(ns streamparse.commands.run
  "Run a topology on a Storm LocalCluster."
  (:require [clojure.string :as string]
            [streamparse.cli :refer [cli]]
            [clojure.stacktrace :refer [print-stack-trace]]
            [clojure.core :refer [fn?]]
            [clojure.data.json :as json])
  (:use [backtype.storm clojure config])
  (:import  [backtype.storm LocalCluster])
  (:gen-class))


(defn run-local! [topology-file options run-for-secs]
  "Run the topology locally via LocalCluster. The topology definition is
  contained inside of topology-file which is assume to have a single var
  defined which contains the topology definition."
  (try
    (let [topology-def (load-file topology-file) ; should only be a single var
          topology-var (var-get topology-def)
          ; only pass options if topology-var is a function (not just callable)
          topology (apply topology (if (fn? topology-var) (topology-var options) topology-var))
          topology-name (str (:name (meta topology-def)))
          cluster (LocalCluster.)]
      (.submitTopology cluster
                       topology-name
                       options
                       topology)
      ;; sleep for a few seconds to let the topology run locally
      (Thread/sleep (if (= 0 run-for-secs) Integer/MAX_VALUE run-for-secs))
      ;; shutdown the cluster
      (.shutdown cluster))
    (catch Exception e
      ((println (str "Caught exception: " (.getMessage e) \newline))
       (print-stack-trace e)))))


(defn usage []
  (->> ["sparsej run <topology_spec_file>"
        ""
        "Run a topology locally (no Storm cluster needed)."
        ""]
        (string/join \newline)))

(defn smart-read-str [val]
  "Read JSON string and don't convert git hashes to numbers"
  ;; issue with literals that start with digits, but contain letters
  (if (not= (re-find #"\d+[A-Za-z]" val) nil)
    val
    (try
      (json/read-str val)
      (catch Exception e val))))

(defn -parse-topo-option [val-str]
  "Parse topology --option in option.key=val form."
  (let [[key val] (string/split val-str #"=")
       parsed-val (smart-read-str val)]
       {key parsed-val}))

(defn -assoc-topo-option [previous key val]
  "Associate topology --option with option map."
  (assoc previous key
    (if-let [oldval (get previous key)]
      (merge oldval val)
      val)))

(defn -main [& args]
  (let [[opts args banner]
         (cli args
              ["-h" "--help" "Show this help screen." :flag true :default false]
              ["-d" "--debug" "Run with debug mode." :flag true :default false]
              ["-t" "--time" "Amount of seconds to run cluser before shutting down. If time <= 0, run indefinitely." :default 0 :parse-fn #(Integer/parseInt %)]
              ["-o" "--option" "Override topology config option."
                :parse-fn -parse-topo-option :assoc-fn -assoc-topo-option])
        ]
    (when (or (= (count args) 0) (:help opts))
      (println (usage))
      (println banner)
      (System/exit 0))
    (let [topology-spec-file (first args)
          ;; set some default options
          defaults  {TOPOLOGY-DEBUG (:debug opts)
                     TOPOLOGY-WORKERS 2
                     TOPOLOGY-ACKER-EXECUTORS 2
                     TOPOLOGY-MAX-SPOUT-PENDING 5000
                     TOPOLOGY-MESSAGE-TIMEOUT-SECS 60}
          ;; overlay provided options
          options (merge defaults (:option opts))
          run-for-secs (* (:time opts) 1000)]
      (run-local! topology-spec-file options run-for-secs))))
