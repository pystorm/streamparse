(defproject com.parsely/streamparse "0.0.3-SNAPSHOT"
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
  :dependencies [[commons-collections/commons-collections "3.2.1"]]
  :profiles {:dev
              {:dependencies [
                              [org.apache.storm/storm-core "0.9.1-incubating"]
                              [org.clojure/data.json "0.2.4"]
                              [org.testng/testng "6.8.5"]
                              [org.easytesting/fest-assert-core "2.0M8"]
                              [org.mockito/mockito-all "1.9.0"]
                              [org.jmock/jmock "2.6.0"]]
               }}
  :source-paths ["src"]
  :test-paths ["test"]
  :resource-paths ["resources"]
  :aot :all)
