"""
Pixel count topology
"""

from streamparse import Grouping, JavaSpout, Topology

from bolts.pixel_count import PixelCounterBolt
from bolts.pixel_deserializer import PixelDeserializerBolt


class PixelCount(Topology):
    pixel_spout = JavaSpout.spec(
        name="pixel-spout",
        full_class_name="pixelcount.spouts.PixelSpout",
        args_list=[],
        outputs=["pixel"],
    )
    pixel_deserializer = PixelDeserializerBolt.spec(
        name="pixel-deserializer-bolt", inputs=[pixel_spout]
    )
    pixel_counter = PixelCounterBolt.spec(
        name="pixel-count-bolt",
        inputs={pixel_deserializer: Grouping.fields("url")},
        config={"topology.tick.tuple.freq.secs": 1},
    )
