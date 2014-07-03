(ns streamparse.specs
  (:use     [backtype.storm.clojure])
  (:gen-class))

(defn python-spout-spec [options class_name & args]
  (apply
    shell-spout-spec
    (concat [[(get options "topology.python.path" "python")
              "-m" "streamparse.run" class_name]]
            args)
  )
)

(defn python-bolt-spec [options inputs class_name & args]
  (apply
    shell-bolt-spec
    (concat [inputs
             [(get options "topology.python.path" "python")
              "-m" "streamparse.run" class_name]]
            args)
  )
)
