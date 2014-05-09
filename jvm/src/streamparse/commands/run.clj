(ns streamparse.commands.run
  "Run a topology on a Storm LocalCluster."
  (:require [clojure.string :as string]
            [clojure.tools.cli :refer [cli]]
            [clojure.stacktrace :refer [print-stack-trace]])
  (:use [backtype.storm clojure config])
  (:import  [backtype.storm LocalCluster])
  (:gen-class))


(defn run-local! [topology-file debug run-for-secs]
  "Run the topology locally via LocalCluster. The topology definition is
  contained inside of topology-file which is assume to have a single var
  defined which contains the topology definition."
  (println (str "Running " topology-file " for " run-for-secs))
  (try
    (let [topology-def (load-file topology-file) ; should only be a single var
          topology (apply topology (var-get topology-def))
          topology-name (str (:name (meta topology-def)))
          cluster (LocalCluster.)]
      (.submitTopology cluster
                       topology-name
                       {TOPOLOGY-DEBUG debug}
                       topology)
      ;; sleep for a few seconds to let the topology run locally
      (Thread/sleep run-for-secs)
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


(defn -main [& args]
  (let [[opts args banner]
         (cli args
              ["-h" "--help" "Show this help screen." :flag true :default false]
              ["-d" "--debug" "Run with debug mode." :flag true :default false]
              ["-t" "--time" "Amount of seconds to run cluser before shutting down." :default 5 :parse-fn #(Integer/parseInt %)])]
    (when (or (= (count args) 0) (:help opts))
      (println (usage))
      (println banner)
      (System/exit 0))
    (let [topology-spec-file (first args)
          run-for-secs (* (:time opts) 1000)]
      (run-local! topology-spec-file (:debug opts) run-for-secs))))
