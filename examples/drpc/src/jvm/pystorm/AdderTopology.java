package streamparse;

import java.util.Map;

import backtype.storm.Config;
import backtype.storm.LocalCluster;
import backtype.storm.LocalDRPC;
import backtype.storm.StormSubmitter;
import backtype.storm.coordination.BatchOutputCollector;
import backtype.storm.drpc.LinearDRPCTopologyBuilder;
import backtype.storm.task.TopologyContext;
import backtype.storm.task.ShellBolt;
import backtype.storm.topology.IRichBolt;
import backtype.storm.topology.BasicOutputCollector;
import backtype.storm.topology.OutputFieldsDeclarer;
import backtype.storm.topology.base.BaseBasicBolt;
import backtype.storm.topology.base.BaseBatchBolt;
import backtype.storm.tuple.Fields;
import backtype.storm.tuple.Tuple;
import backtype.storm.tuple.Values;


public class AdderTopology {

    public static class AdderBolt extends ShellBolt implements IRichBolt {
        public AdderBolt() {
            super("python", "adder.py");
        }

        @Override
        public void declareOutputFields(OutputFieldsDeclarer declarer) {
            declarer.declare(new Fields("id", "result"));
        }

        @Override
        public Map<String, Object> getComponentConfiguration() {
            return null;
        }
    }


    public static void main(String[] args) {
        LinearDRPCTopologyBuilder builder = new LinearDRPCTopologyBuilder("adder");
        builder.addBolt(new AdderBolt(), 1);

        Config conf = new Config();
        if (args == null || args.length == 0) {
            LocalDRPC drpc = new LocalDRPC();
            LocalCluster cluster = new LocalCluster();
            cluster.submitTopology("drpc-adder", conf, builder.createLocalTopology(drpc));

            System.out.println("\nResult for 1 + 1 = " + drpc.execute("adder", "1 1") + "\n");
            System.out.println("\nResult for 50 + 50 = " + drpc.execute("adder", "50 50") + "\n");
            System.out.println("\nResult for -100 + 100 = " + drpc.execute("adder", "-100 100") + "\n");

            cluster.shutdown();
            drpc.shutdown();
        }
        else {
            //conf.setNumWorkers(3);
            //StormSubmitter.submitTopology(args[0], conf, builder.createRemoteTopology());
        }
    }
}