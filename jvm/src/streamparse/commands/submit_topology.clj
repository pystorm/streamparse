(ns streamparse.commands.submit_topology
  "Submit a topology to a Storm cluster."
  (:require [clojure.string :as string]
            [streamparse.cli :refer [cli]]
            [clojure.stacktrace :refer [print-stack-trace]]
            [clojure.core :refer [fn?]]
            [clojure.data.json :as json])
  (:use [backtype.storm clojure config])
  (:import  [backtype.storm StormSubmitter])
  (:gen-class))


(defn submit-topology! [topology-file options]
  "Submit a topology to a Storm cluster. The topology definition is contained
  inside of topology-file which is assumed to have a single var defined which
  contains the topology definition."
  (try
    (let [topology-def (load-file topology-file) ; should only be a single var
          topology-var (var-get topology-def)
          ; only pass options if topology-var is a function (not just callable)
          topology (apply topology (if (fn? topology-var) (topology-var options) topology-var))
          topology-name (str (:name (meta topology-def)))]
       (StormSubmitter/submitTopology topology-name
                                      options
                                      topology))
    (catch Exception e
      ((println (str "Caught exception: " (.getMessage e) \newline))
       (print-stack-trace e)))))


(defn usage []
  (->> ["sparsej submit <topology_spec_file>"
        ""
        "Submit a topology to a remote storm cluster."
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

(defn -main [& sysargs]
  (let [[opts args banner]
         (cli sysargs
              ["-h" "--help" "Show this help screen." :flag true :default false]
              ["-n" "--host" "Hostname for Nimbus." :default "localhost"]
              ["-p" "--port" "Port for Nimbus." :default 6627 :parse-fn #(Integer/parseInt %)]
              ["-d" "--debug" "Enable debugging for the cluster." :flag true :default false]
              ["-o" "--option" "Override topology config option."
                :parse-fn -parse-topo-option :assoc-fn -assoc-topo-option])]
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
                     NIMBUS-HOST (:host opts)
                     NIMBUS-THRIFT-PORT (:port opts)
                     TOPOLOGY-MESSAGE-TIMEOUT-SECS 60}
          ;; overlay provided options
          options (merge defaults (:option opts))
          ]
      (println opts)
      (submit-topology! topology-spec-file options))))
