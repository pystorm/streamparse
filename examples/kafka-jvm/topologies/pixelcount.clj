(ns pixelcount
  (:use [backtype.storm.clojure]
        [pixelcount.spouts.pixel_spout :only [spout] :rename {spout pixel-spout}]
        [streamparse.specs])
  (:gen-class))


(defn pixelcount [options]
   [
    ;; spout configurations
    {"pixel-spout" (spout-spec pixel-spout :p 1)}

    ;; bolt configurations
    {
      ;; Technically, this bolt isn't really needed, just need to add a proper
      ;; deserializer to Kafka spout so that it doesn't stupidly treat all
      ;; messages as strings, but this is fine for a demo
      "pixel-deserializer-bolt" (python-bolt-spec
        options
        {"pixel-spout" :shuffle}
        "bolts.pixel_deserializer.PixelDeserializerBolt"
        ["ip" "ts" "url"]
        :p 1)

      "pixel-count-bolt" (python-bolt-spec
        options
        ;; fields grouping on url
        {"pixel-deserializer-bolt" ["url"]}
        "bolts.pixel_count.PixelCounterBolt"
        ;; terminal bolt
        []
        :p 1
        :conf {"topology.tick.tuple.freq.secs", 1})
    }
  ]
)
