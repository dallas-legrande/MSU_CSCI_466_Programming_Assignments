'''
    Chris Cooper and Dallas LeGrande
    CSCI 466
    Assignment 3
'''

import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = 50

    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None

    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)


## Implements a network layer packet (different from the RDT packet
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths
    dst_addr_S_length = 5
    # extended to include sequence number of packet and flags field
    sequence_num_field = 6
    flags_field = 7

    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, dst_addr, data_S, sequence_num, flags):
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.sequence_num = sequence_num
        self.flags = flags

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.sequence_num)
        byte_S += str(self.flags)
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0 : NetworkPacket.dst_addr_S_length])
        sequence_num = int(byte_S[NetworkPacket.dst_addr_S_length: NetworkPacket.sequence_num_field])
        flags = int(byte_S[NetworkPacket.sequence_num_field:NetworkPacket.flags_field])
        data_S = byte_S[NetworkPacket.flags_field:]
        return self(dst_addr, data_S, sequence_num, flags)

## Implements a network host for receiving and transmitting data
class Host:

    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination

    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)

    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        MTU = self.out_intf_L[0].mtu - NetworkPacket.flags_field
        packet_counter = 0

        # adjust MTU for extra encoded fields (flag and sequence number)
        MTU_adj = MTU - NetworkPacket.flags_field
        if len(data_S) > (MTU - NetworkPacket.flags_field):
            packet_size = (int(len(data_S) / MTU_adj) + 1)
        else:
            packet_size = 1
        pack_size_begin = 0
        packet_counter += 1
        pack_size_end = MTU_adj

        for i in range(packet_size):
            if pack_size_end > len(data_S):
                pack_size_end = len(data_S)
            if i != packet_size - 1:
                p = NetworkPacket(dst_addr, data_S[pack_size_begin:pack_size_end], packet_counter, 1)
            else:
                p = NetworkPacket(dst_addr, data_S[pack_size_begin:pack_size_end], packet_counter, 0)

            self.out_intf_L[0].put(p.to_byte_S())  # send packets always enqueued successfully
            print('%s: sending packet "%s" on the out interface with mtu=%d\n' % (self, p, self.out_intf_L[0].mtu))
            pack_size_begin += MTU_adj
            pack_size_end += MTU_adj

    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            print('%s: received packet "%s" on the in interface ' % (self, pkt_S))

    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return


## Implements a multi-interface router described in class
class Router:

    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    #method to route interfaces on links to correct links
    def route_table(self, dst):
        if dst == "00004":
            if self.name == 'A':
                from_interface = 1
            elif self.name == 'C':
                from_interface = 0
            elif self.name == 'D':
                from_interface = 1

        else:
            from_interface = 0

        return from_interface

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    ## appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
                    # improve forwarding to forward to appropriate interface, not just i
                    MTU = self.out_intf_L[0].mtu - NetworkPacket.flags_field
                    data_S = pkt_S[NetworkPacket.flags_field:]
                    dst_addr = pkt_S[0:NetworkPacket.dst_addr_S_length]
                    packet_counter = pkt_S[NetworkPacket.dst_addr_S_length:NetworkPacket.sequence_num_field]
                    out_inf = self.route_table(dst_addr)

                    if (len(data_S) > (MTU - NetworkPacket.flags_field)):
                        packet_size = (int(len(data_S) / MTU) + 1)
                    else:
                        packet_size = 1
                    pack_size_begin = 0
                    pack_size_end = MTU

                    for i in range(packet_size):
                        if (pack_size_end > len(data_S)):
                            pack_size_end = len(data_S)
                        if (i != (packet_size - 1)):
                            p = NetworkPacket(dst_addr, data_S[pack_size_begin:pack_size_end], packet_counter, 1)
                        else:
                            p = NetworkPacket(dst_addr, data_S[pack_size_begin:pack_size_end], packet_counter, 0)

                        self.out_intf_L[out_inf].put(p.to_byte_S(), True) #send packets always enqueued successfully
                        print('%s: sending packet "%s" on the out interface %d with mtu=%d\n' % (self, p, out_inf, MTU))
                        pack_size_begin += MTU
                        pack_size_end += MTU

                    # print('%s: forwarding packet "%s" from interface %d to %d with mtu %d\n' % (self, p, i, i, self.out_intf_L[0].mtu))

            except queue.Full:
                print('%s: packet "%s" lost on interface %d\n' % (self, p, i))
                pass

    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return
