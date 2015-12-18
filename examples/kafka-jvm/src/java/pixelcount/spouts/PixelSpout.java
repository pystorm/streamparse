package pixelcount.spouts;

import storm.kafka.SpoutConfig;
import storm.kafka.KafkaSpout;
import storm.kafka.StringScheme;
import storm.kafka.ZkHosts;
import backtype.storm.spout.SchemeAsMultiScheme;

public class PixelSpout extends KafkaSpout {

	public PixelSpout(SpoutConfig spoutConf) {
		super(spoutConf);
	}

	public PixelSpout() {
		this(PixelSpout.defaultSpoutConfig());
	}

	public static SpoutConfig defaultSpoutConfig() {
		ZkHosts hosts = new ZkHosts("streamparse-box:2181", "/brokers");
		SpoutConfig spoutConf = new SpoutConfig(hosts, "pixels", "/kafka_storm", "pixel_reader");
		spoutConf.scheme = new SchemeAsMultiScheme(new StringScheme());
		spoutConf.forceFromStart = true;
		return spoutConf;
	}
}
