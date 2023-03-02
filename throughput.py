from ryu.lib.packet import ethernet, packet
import time
import customCtrl


# Khởi tạo biến global để lưu trữ thông tin các packet đã gửi đi và nhận về
sent_packets = {}
received_packets = {}
controller =customCtrl.customCtrl()
# Hàm xử lý khi nhận được packet từ switch
def packet_in_handler(event):
    msg = event.msg
    datapath = msg.datapath
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    in_port = msg.match['in_port']

    # Lấy thông tin packet và tính toán thông lượng
    pkt = packet.Packet(msg.data)
    eth = pkt.get_protocol(ethernet.ethernet)

    # Lấy thời gian hiện tại
    current_time = time.time()

    # Xử lý thông tin packet đến
    if eth.dst == controller.mac_to_port[datapath.id][eth.dst]:
        if eth.dst not in received_packets:
            received_packets[eth.dst] = []
        received_packets[eth.dst].append(current_time)

    # Xử lý thông tin packet đi
    if eth.src not in sent_packets:
        sent_packets[eth.src] = []
    sent_packets[eth.src].append(current_time)

# Hàm tính throughput cho mỗi địa chỉ MAC
def calculate_throughput(mac_address):
    total_bytes = 0
    last_time = None

    # Tính tổng số byte và khoảng thời gian giữa packet cuối cùng và packet đầu tiên
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
        return throughput

    return 0  # Trường hợp không có packet nào gửi hoặc nhận

# Sử dụng hàm calculate_throughput để tính toán throughput cho từng địa chỉ MAC
def get_throughput():
    result = {}
    for mac_address in sent_packets.keys():
        throughput = calculate_throughput(mac_address)
        result[mac_address] = throughput
    return result

def main():
    # Tạo một đối tượng Throughput

    # Gọi các phương thức để tính toán và hiển thị thông tin
    for mac in controller.mac_address:
        calculate_throughput(mac)
        res = get_throughput()
        print("Result: %s", res)

if __name__ == '__main__':
    main()