(defproject com.parsely/streamparse "0.0.4-SNAPSHOT"
  :description "Command line utilities for the Python streamparse library needed for JVM/Thrift interop with Storm clusters."
  :url "https://github.com/Parsely/streamparse"
  :mailing-list {:name "streamparse"
                 :archive "https://groups.google.com/forum/#!forum/streamparse"
                 :subscribe "streamparse+subscribe@googlegroups.com"
                 :unsubscribe "streamparse+unsubscribe@googlegroups.com"
                 :post "streamparse@googlegroups.com"}
  :license {:name "Apache 2.0"
            :url "https://raw.githubusercontent.com/Parsely/streamparse/master/LICENSE"
            :distribution :repo}
  :min-lein-version "2.0.0"
  :dependencies [
                 [org.clojure/clojure  "1.5.1"]
                 [org.clojure/data.json "0.2.6"]
                 [org.apache.storm/storm-core "0.9.4"]
                 ]
  :source-paths ["src"]
  :test-paths ["test"]
  :resource-paths ["resources"]
  :aot :all
  )