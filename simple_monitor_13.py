from operator import attrgetter

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

from datetime import datetime
import csv
import time
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

sent_packets = {}
received_packets = {}
class SimpleMonitor13(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(SimpleMonitor13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.packet_count = 0
        self.packets = []
        self.rxflow = []
        self.txflow = []
        self.csv_file_name = 'packet_stats.csv'
        self.rxflow_file_name = 'rx_flow.csv'
        self.txflow_file_name = 'tx_flow.csv'
        self.mac_address = []
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)


    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
                self.save_rxflows()
                self.save_txflows()
            hub.sleep(5)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         '
                         'in-port  eth-dst           '
                         'out-port packets  bytes')
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['in_port'], stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)
            self.rxflow.append((ev.msg.datapath.id,stat.port_no, stat.rx_packets, stat.rx_bytes, stat.rx_errors))
            self.txflow.append((ev.msg.datapath.id,stat.port_no, stat.tx_packets, stat.tx_bytes, stat.tx_errors))
            




    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        in_port = msg.match['in_port']
        datapath = msg.datapath
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        self.packet_count += 1
        now = datetime.now()
        pkt = packet.Packet(ev.msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)


        if eth:
            self.mac_address.append(eth.src)
            #self.logger.info("Time: %s Source: %s Destination: %s In port: %s ", now, eth.src, eth.dst, in_port)
            self.packets.append((now, eth.src, eth.dst, in_port))
            self.save_packet()


            
    def save_packet(self):
        with open(self.csv_file_name, mode='w') as csv_file:
            fieldnames = ['Timestamp', 'Source MAC', 'Destination MAC', 'In Port']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for p in self.packets:
                writer.writerow({'Timestamp': p[0], 'Source MAC': p[1], 'Destination MAC': p[2], 'In Port': p[3]})
    
    def save_rxflows(self):
        with open(self.rxflow_file_name, mode='w') as csv_file:
            fieldnames = ['Datapath ID', 'Port', 'rx Packets', 'rx Bytes', 'rx Errors']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for r in self.rxflow:
                writer.writerow({'Datapath ID': r[0], 'Port': r[1], 'rx Packets': r[2], 'rx Bytes': r[3], 'rx Errors': r[4]})
    def save_txflows(self):
        with open(self.txflow_file_name, mode='w') as csv_file:
            fieldnames = ['Datapath ID', 'Port', 'tx Packets', 'tx Bytes', 'tx Errors']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for t in self.txflow:
                writer.writerow({'Datapath ID': t[0], 'Port': t[1], 'tx Packets': t[2], 'rx Bytes': t[3], 'rx Errors': t[4]})
                