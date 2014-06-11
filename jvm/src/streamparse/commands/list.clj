(ns streamparse.commands.list
  "List topologies command for streamparse."
  (:require [clojure.string :as string]
            [streamparse.cli :refer [cli]]
            [clojure.pprint :refer [print-table]]
            [clojure.data.json :as json]
            [backtype.storm.thrift :refer :all])
  (:import [backtype.storm.generated TopologySummary])
  (:gen-class))


(defn topologies-as-map [hostname port]
  "Fetch all topologies from a Nimbus cluster assumed to be running on
  localhost and return as a vector of maps with topology information"
  (with-nimbus-connection [nimbus hostname port]
    (let [cluster-info (.getClusterInfo nimbus)
          topologies (.get_topologies cluster-info)]
      (vec (map #(hash-map :id (.get_id %)
                           :name (.get_name %)
                           :status (.get_status %)
                           :num-workers (.get_num_workers %)
                           :num-tasks (.get_num_tasks %)
                           :num-executors (.get_num_executors %)
                           :uptime-secs (.get_uptime_secs %)) topologies)))))


(defn list-topologies [hostname port {:keys [as-json] :or {as-json false}}]
  "List all running topologies for a Nimbus cluster assumed to be running on
  localhost either as JSON or a pretty-printed table."
  (let [topologies (topologies-as-map hostname port)]
    (if (or (nil? topologies) (empty? topologies))
      (println "No topologies running.")
      (if as-json
        (println (json/write-str topologies))
        (print-table [:name :status :num-workers :num-executors :num-tasks :uptime-secs]
                     topologies)))))


(defn usage []
  (->> ["sparsej list"
        ""
        "List topologies."
        ""]
        (string/join \newline)))


(defn -main [& args]
  (let [[opts args banner]
         (cli args
              ["-h" "--help" "Show this help screen." :flag true :default false]
              ["-j" "--json" "Show output as JSON." :flag true :default false]
              ["-n" "--host" "Hostname for Nimbus." :default "localhost"]
              ["-p" "--port" "Port for Nimbus." :default 6627 :parse-fn #(Integer/parseInt %)])]
    (when (:help opts)
      (println (usage))
      (println banner)
      (System/exit 0))
    (list-topologies (:host opts) (:port opts) {:as-json (:json opts)})))
