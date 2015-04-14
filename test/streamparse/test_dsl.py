import logging
from streamparse.dsl.topology import Topology, Spec, Grouping
from streamparse.storm.spout import Spout
from streamparse.storm.bolt import Bolt

log = logging.getLogger(__name__)


class WordSpout(Spout):
    streams = ["word"]


class WordCountBolt(Bolt):
    streams = ["word", "count"]


class WordCount(Topology):
    word_spout = Spec(
        WordSpout,
        parallelism=2)
    word_count_bolt = Spec(
        WordCountBolt,
        source="word_spout",
        group_on=Grouping.fields("word"),
        parallelism=8)


def test_wordcount_topology():
    assert len(WordCount.specs) == 2
    for component in WordCount.specs:
        if component.cls == WordCountBolt:
            assert component.group_on == ["word"]
