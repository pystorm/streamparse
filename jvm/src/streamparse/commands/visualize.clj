(ns streamparse.commands.visualize
  "Visualize a topology."
  (:require [clojure.string :as string]
            [streamparse.cli :refer [cli]]
            [clojure.stacktrace :refer [print-stack-trace]])
  (:use [backtype.storm clojure config]
        ;;[storm-spirit.core] <-- removed, need to wait for 1.5 XXX
  )
  (:import  [backtype.storm LocalCluster])
  (:gen-class))

(defn build-topology [topology-path]
  "Load, compile, and build Storm topology."
  (apply topology (var-get (load-file topology-path))))

(defn vis [topology-path & [opts]]
  "Use storm-spirit to visualize the topology with graphviz."
  ;; (visualize-with-graphviz (build-topology topology-path) opts) <-- removed
  (println (str "visualizing [" topology-path "]"))
  (println "ERROR: storm-spirit not supported yet, waiting for Storm / Clojure 1.5 upgrade")
  )

(defn vis-vertical [topology-path]
  "Vertical visualization (default)."
  (vis topology-path))

(defn vis-horizontal [topology-path]
  "Horizontal visualization."
  (vis topology-path {:graph-attrs {:rankdir :LR}}))

(defn usage []
  (->> ["sparsej visualize <topology_spec_file>"
        ""
        "Compile and visualize a topology."
        ""]
        (string/join \newline)))

(defn -main [& args]
  (let [[opts args banner]
         (cli args
              ["-h" "--help" "Show this help screen." :flag true :default false]
              ["-f" "--flip" "Flip visualization to be horizontal." :flag true :default false]
              )
        ]
    (when (or (= (count args) 0) (:help opts))
      (println (usage))
      (println banner)
      (System/exit 0))
    (let [topology-spec-file (first args)
          vis-fn (if (:flip opts)
                   vis-horizontal
                   vis-vertical)]
      (vis-fn topology-spec-file)
      (System/exit 0)
      )))
