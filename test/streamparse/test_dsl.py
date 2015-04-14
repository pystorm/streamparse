from streamparse.dsl.topology import Topology, ComponentSpec, Grouping

import logging

log = logging.getLogger(__name__)


class MockComponent(object):

    @classmethod
    def spec(cls,
             name=None,
             parallelism=1,
             source=None,
             group_on=None):
        d = {
            "parallelism": parallelism,
            "group_on": group_on,
            "source": source,
            "class": cls,
            "streams": cls.streams
        }
        if name is not None:
            d["name"] = name
        return ComponentSpec(d)


class WordSpout(MockComponent):
    streams = ["word"]


class WordCountBolt(MockComponent):
    streams = ["word", "count"]


class WordCount(Topology):
    word_spout = WordSpout.spec(
        parallelism=2)
    word_count_bolt = WordCountBolt.spec(
        source="word_spout",
        group_on=Grouping.fields("word"),
        parallelism=8)


def test_wordcount_topology():
    assert len(WordCount.field_list) == 2
    for component in WordCount.field_list:
        if component["class"] == WordCountBolt:
            assert component["group_on"] == ["word"]
