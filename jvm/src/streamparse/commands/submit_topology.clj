(ns streamparse.commands.submit_topology
  "Submit a topology to a Storm cluster."
  (:require [clojure.string :as string]
            [clojure.tools.cli :refer [cli]]
            [clojure.stacktrace :refer [print-stack-trace]])
  (:use [backtype.storm clojure config])
  (:import  [backtype.storm StormSubmitter])
  (:gen-class))


(defn submit-topology! [topology-file debug]
  "Submit a topology to a Storm cluster. The topology definition is contained
  inside of topology-file which is assumed to have a single var defined which
  contains the topology definition."
  (try
    (let [topology-def (load-file topology-file) ; should only be a single var
          topology (apply topology (var-get topology-def))
          topology-name (str (:name (meta topology-def)))]
       (StormSubmitter/submitTopology topology-name
                                      {TOPOLOGY-DEBUG debug
                                       TOPOLOGY-WORKERS 3}
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


(defn -main [& args]
  (let [[opts args banner]
         (cli args
              ["-h" "--help" "Show this help screen." :flag true :default false]
              ["-n" "--host" "Hostname for Nimbus." :default "localhost"]
              ["-p" "--port" "Port for Nimbus." :default 6627 :parse-fn #(Integer/parseInt %)])]
              ["-d" "--debug" "Enable debugging for the cluster." :flag true :default false]
    (when (or (= (count args) 0) (:help opts))
      (println (usage))
      (println banner)
      (System/exit 0))
    (let [topology-spec-file (first args)]
      (submit-topology! topology-spec-file (:debug opts)))))
