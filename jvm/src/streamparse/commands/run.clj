(ns streamparse.commands.run
  "Submit a topology to a Storm cluster."
  (:require [clojure.string :as string]
            [clojure.tools.cli :refer [cli]])
  (:use [backtype.storm clojure config])
  (:import  [backtype.storm LocalCluster])
  (:gen-class))


(defn run-local! [topology-file debug sleep]
  "Run the topology locally via LocalCluster. The topology definition is
  contained inside of topology-file which is assume to have a single var
  defined which contains the topology definition."
  (try
    (let [topology-def (load-file topology-file)
          topology (apply topology (var-get topology-def))
          topology-name (:name (meta topology-def))
          cluster (LocalCluster.)]
      (.submitTopology cluster
                       topology-name
                       {TOPOLOGY-DEBUG debug}
                       topology)
      ;; sleep for a few seconds to let the topology run locally
      (Thread/sleep sleep)
      ;; shutdown the cluster
      (.shutdown cluster))
    (catch Exception e (println (str "Caught exception: " (.getMessage e))))))


(defn usage []
  (->> ["sparsej run <topology_name>"
        ""
        "Run a topology locally (no Storm cluster needed)."
        ""]
        (string/join \newline)))


(defn -main [& args]
  (let [[opts args banner]
         (cli args
              ["-h" "--help" "Show this help screen." :flag true :default false]
              ["-d" "--debug" "Run with debug mode." :flag true :default false]
              ["-s" "--sleep" "Amount of seconds to run cluser before shutting down" :default 5000 :parse-fn #(* (Integer/parseInt %) 1000)])]
    (when (or (= (count args) 0) (:help opts))
      (println (usage))
      (println banner)
      (System/exit 0))
    ;; TODO: Should check to see if topology file exists
    (let [topology-name (first args)]
      (run-local! (str "topologies/" topology-name ".clj") (:debug opts) (:sleep opts)))))
