from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from datetime import datetime
import csv
import time
from ryu.ofproto import ofproto_v1_3_parser

sent_packets = {}
received_packets = {}

class customCtrl(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(customCtrl, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.packet_count = 0
        self.packets = []
        self.csv_file_name = 'packet_stats.csv'
        self.datapaths = {}
        self.flow_stats = {}
        self.mac_address = []
        self.throughput = 0

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        current_time = time.time()

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
            if eth.dst not in received_packets:
                received_packets[eth.dst] = []
            received_packets[eth.dst].append(current_time)
            if eth.src not in sent_packets:
                sent_packets[eth.src] = []
            sent_packets[eth.src].append(current_time)
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]
        


        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)




        # if eth:
        #     # Xử lý thông tin packet đến
        #     if eth.dst == self.mac_to_port[dpid][dst]:
        #         if eth.dst not in received_packets:
        #             received_packets[eth.dst] = []
        #         received_packets[eth.dst].append(current_time)

        #         # Xử lý thông tin packet đi
        #         if eth.src not in sent_packets:
        #             sent_packets[eth.src] = []
        #         sent_packets[eth.src].append(current_time)

        #         self.calculate_throughput()

        
    

    def calculate_throughput(self, ev):
        self.logger.info("Hello")
        pkt = packet.Packet(ev.msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        total_bytes = 0
        last_time = None

        # Tính tổng số byte và khoảng thời gian giữa packet cuối cùng và packet đầu tiên
        mac_address = eth.src
        for t in sent_packets.get(mac_address, []):
            if last_time is None or t > last_time:
                last_time = t
            total_bytes += 1500  # Giả sử tất cả các packet có kích thước 1500 byte

        first_time = None
        for t in received_packets.get(mac_address, []):
            if first_time is None or t < first_time:
                first_time = t

        if first_time is not None and last_time is not None:
            duration = last_time - first_time
            throughput = total_bytes / duration / 1000000  # Đơn vị là Mbps
            print(throughput)
            self.throughput = throughput

    
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
            self.calculate_throughput(ev)
            self.mac_address.append(eth.src)
            self.logger.info("Time: %s Source: %s Destination: %s In port: %s Throughput: %s", now, eth.src, eth.dst, in_port, self.throughput)
            self.packets.append((now, eth.src, eth.dst, in_port))
            self.save_to_csv()


            
    def save_to_csv(self):
        with open(self.csv_file_name, mode='w') as csv_file:
            fieldnames = ['Timestamp', 'Source MAC', 'Destination MAC', 'In Port', 'Throughput']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for p in self.packets:
                writer.writerow({'Timestamp': p[0], 'Source MAC': p[1], 'Destination MAC': p[2], 'In Port': p[3], 'Throughput': self.throughput})
                
            

    def shutdown(self):
        self.save_to_csv()
        self.logger.info("Shutdown Ryu Packet Monitor")






