(defproject {{ project_name }} "0.0.1-SNAPSHOT"
  :source-paths ["topologies"]
  :resource-paths ["_resources"]
  :aot :all
  :target-path "_build"
  :min-lein-version "2.0.0"
  :jvm-opts ["-client"]
  :dependencies [[org.apache.storm/storm-core "0.9.1-incubating"]
                 [com.parsely/streamparse "0.0.1-SNAPSHOT"]
                 [org.clojure/clojure "1.5.1"]
                 [org.clojure/data.json "0.2.4"]
                 [org.clojure/tools.cli "0.3.1"]]
  )
