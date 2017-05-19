(defproject {{ project_name }} "0.0.1-SNAPSHOT"
  :resource-paths ["_resources"]
  :target-path "_build"
  :min-lein-version "2.0.0"
  :jvm-opts ["-client"]
  :dependencies  [[org.apache.storm/storm-core "1.1.0"]
                  [org.apache.storm/flux-core "1.1.0"]]
  :jar-exclusions     [#"log4j\.properties" #"org\.apache\.storm\.(?!flux)" #"trident" #"META-INF" #"meta-inf" #"\.yaml"]
  :uberjar-exclusions [#"log4j\.properties" #"org\.apache\.storm\.(?!flux)" #"trident" #"META-INF" #"meta-inf" #"\.yaml"]
  )
