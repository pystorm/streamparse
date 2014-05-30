(defproject {{ project_name }} "0.0.1-SNAPSHOT"
  :source-paths ["topologies"]
  :resource-paths ["_resources"]
  :target-path "_build"
  :min-lein-version "2.0.0"
  :jvm-opts ["-client"]
  :dependencies [     [org.clojure/data.json "0.2.4"]
                      [org.clojure/tools.cli "0.3.1"]
                      [org.apache.storm/storm-core "0.9.1-incubating"]
                      [com.parsely/streamparse "0.0.2-SNAPSHOT"]]
  :jar-exclusions     [#"log4j\.properties" #"backtype" #"trident" #"META-INF" #"meta-inf" #"\.yaml"]
  :uberjar-exclusions [#"log4j\.properties" #"backtype" #"trident" #"META-INF" #"meta-inf" #"\.yaml"]
  )
