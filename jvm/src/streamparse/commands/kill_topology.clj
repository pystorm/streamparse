(ns streamparse.commands.kill_topology
  "List topologies command for streamparse."
  (:require [clojure.string :as string]
            [streamparse.cli :refer [cli]]
            [clojure.data.json :as json]
            [backtype.storm.thrift :refer :all])
  (:import [backtype.storm.generated KillOptions NotAliveException])
  (:gen-class))


(defn kill-topology [hostname port topology-name {:keys [wait]}]
  "Kill a topology with a given name and optionally, an amount of time to
  wait."
  (let [opts (KillOptions.)]
    (if wait (.set_wait_secs opts wait))
    (with-nimbus-connection [nimbus hostname port]
      (.killTopologyWithOpts nimbus topology-name opts)
      (println "Killed topology: " topology-name))))


(defn usage []
  (->> ["sparsej kill <topology_name>"
        ""
        "Kill a specific topology."
        ""]
        (string/join \newline)))


(defn -main [& args]
  (let [[opts args banner]
         (cli args
              ["-h" "--help" "Show this help screen." :flag true :default false]
              ["-w" "--wait" "Amount of time to wait for topology to gracefully stop." :parse-fn #(Integer/parseInt %)]
              ["-n" "--host" "Hostname for Nimbus." :default "localhost"]
              ["-p" "--port" "Port for Nimbus." :default 6627 :parse-fn #(Integer/parseInt %)])]
    (when (or (not= (count args) 1) (:help opts))
      (println (usage))
      (println banner)
      (System/exit 1))
    (let [topology-name (get args 0)]
      (try
        (kill-topology (:host opts) (:port opts) topology-name
                       {:wait (:wait opts)})
        (catch NotAliveException e
          (println (str "Topology \"" topology-name "\" is not running on "
                        (:host opts) ":" (:port opts) "."))
          (System/exit 1))))))
