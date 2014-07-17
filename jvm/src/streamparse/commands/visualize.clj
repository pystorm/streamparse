(ns streamparse.commands.visualize
  "Visualize a topology."
  (:require [clojure.string :as string]
            [streamparse.cli :refer [cli]]
            [clojure.stacktrace :refer [print-stack-trace]])
  (:use [backtype.storm clojure config]
        ;; [storm-spirit.core] <-- pulls in wrong version of Storm
  )
  (:import  [backtype.storm LocalCluster])
  (:gen-class))

(defn build-topology [topology-path]
  "Load, compile, and build Storm topology."
  (apply topology (var-get (load-file topology-path))))

(defn vis [topology-path & [opts]]
  "Use storm-spirit to visualize the topology with graphviz."
  (println (str "visualizing [" topology-path "]"))
  ;; (visualize-with-graphviz (build-topology topology-path) opts) <-- storm-spirit adds this
  (println "ERROR: cannot actually visualize since streamparse can't bundle storm-spirit yet")
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
