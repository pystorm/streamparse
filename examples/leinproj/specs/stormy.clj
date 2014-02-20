(ns stormy 
  (:use [clojure.tools.cli :only (cli)])
  ;; various utilities
  (:require [clojure.string :as str]
            [clojure.data.json :as json]
            [clojure.java.io :as io])
  ;; Clojure DSL for Storm
  (:use     [backtype.storm clojure config])
  ;; Storm local cluster testing framework
  (:import  [backtype.storm StormSubmitter LocalCluster])
  (:gen-class :main true))

(defn run-local! [topology-file debug]
  (try 
    (let [cluster (LocalCluster.)]
      ;; submit the topology configured above
      (.submitTopology cluster 
                      ;; topology name (arbitrary)
                      "topology-local"
                      ;; topology settings
                      {TOPOLOGY-DEBUG debug} 
                      ;; topology configuration
                      (apply topology (var-get (load-file topology-file))))
      ;; sleep for 5 seconds before...
      (Thread/sleep 5000)
      ;; shutting down the cluster
      (.shutdown cluster)
      ) 
    (catch RuntimeException rte (str "caught exception: " (.getMessage rte)))))

(defn run
  "Print out the options and the arguments"
  [opts args]
  (println (str "Options:\n" opts "\n"))
  (println (str "Arguments:\n" args "\n"))
  (println (apply topology (var-get (load-file (:spec opts)))))
  (run-local! (:spec opts) (:debug opts))
)

(defn -main [& args]
  (let [[opts args banner]
        (cli args
             ["-h" "--help" "Show help" :flag true :default false]
             ["-v" "--verbose" "Verbose output" :flag true :default false]
             ["-s" "--spec" "REQUIRED: Storm Topology spec clj file"]
             ["-j" "--jar" "REQUIRED: Storm Topology code jar file"]
             ["-c" "--config" "Storm Environment config FILE" :default "config.json"]
             ["-d" "--debug" "Enable Storm Topology debugging" :default true]
             ["-e" "--env" "Environment, e.g. prod or local" :default "local"]
             )]
    (when (:help opts)
      (println banner)
      (System/exit 0))
    (if
        (and
         (:spec opts)
         (:env opts)
)
      (do
        (println "")
        (run opts args))
      (println banner))))
