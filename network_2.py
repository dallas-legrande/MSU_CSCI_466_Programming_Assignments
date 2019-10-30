'''
Created on Oct 12, 2016

@author: mwittie
'''
import queue
import threading
import re
import random


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None
    
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
    ## packet encoding lengths. 5 character address length
    dst_addr_S_length = 5
    
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, dst_addr, data_S, id, data_S_Length, offset, more_frag):
        self.dst_addr = dst_addr
        self.data_S = data_S
#        self.frag = {"id": id,
#                     "data_S_Length": data_S_Length,
#                     "offset": offset,
#                     "more_Frag": more_frag}
        self.id = id #"id"+str(id)
        self.data_S_Length = data_S_Length #"data_S_Length"+str(data_S_Length)
        self.offset = offset #"offset"+str(offset)
        self.more_Frag = more_frag #"more_frag"+str(more_frag)
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += self.id.to_bytes(1, byteorder='big')
        byte_S += self.data_S_Length.to_bytes(1, byteorder='big')
        byte_S += self.offset.to_bytes(1, byteorder='big')
        byte_S += self.more_Frag.to_bytes(1, byteorder='big')
        byte_S += self.data_S
        return byte_S

#    def get_pkt_info(byte_S):
#        return byte_S.data_S, byte_S.id, byte_S.data_S_Length, byte_S.offset

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
#        dta, id, ds, off = self.get_pkt_info(byte_S)
        #byte_S.decode('utf-8')
        inc = NetworkPacket.dst_addr_S_length
        a = 8  #byte size
        print("0-inc")
        print(byte_S[0 : inc])
        print("inc-inc+1")
        print(int(byte_S[inc: inc + a].from_bytes(1, byteorder='big')))
        print("inc + 1: inc + 2")
        print(int(byte_S[inc + a: inc + (2*a)].from_bytes(1, byteorder='big')))
        print("inc + 2: inc + 3")
        print(int(byte_S[inc + (2*a): inc + (3*a)].from_bytes(1, byteorder='big')))
        print("inc + 3: inc + 4")
        print(int(byte_S[inc + (3*a): inc + (4*8)].from_bytes(1, byteorder='big')))
        print("inc + 4:")
        print(byte_S[inc + (4*a):])
        dst_addr = int(byte_S[0 : inc])
        frag = {"id": int(byte_S[inc: inc + a].from_bytes(1, byteorder='big')),
                "data_S_Length": int(byte_S[inc + a: inc + (2*a)].from_bytes(1, byteorder='big')),
                "offset": int(byte_S[inc + (2*a): inc + (3*a)].from_bytes(1, byteorder='big')),
                "more_Frag": int(byte_S[inc + (3*a): inc + (4*8)].from_bytes(1, byteorder='big'))},
        data_S = byte_S[inc + (4*8): ]
        return self(dst_addr, data_S, frag)


    

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

    #split the data being sent into smaller packets size of the max size initialized in constructor
    #return the list with the data split and the length of the list
    def split_data(self, data_S, mtu_S):
        sm_p = [(data_S[i:i+mtu_S]) for i in range(0, len(data_S), mtu_S)]
        sm_p_length = len(sm_p)
        return sm_p, sm_p_length

    #get a random id number in the range of 1-255 to identify the fragmented packets
    def get_id(self):
        return random.randint(1, 255)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    #break large packets up into smaller packets
    def udt_send(self, dst_addr, data_S):
        id_num = self.get_id()
        sm_p, sm_p_length = self.split_data(data_S, self.out_intf_L[0].mtu - NetworkPacket.dst_addr_S_length - 38)
        for count, i in enumerate(sm_p):
            print("this is what is needed for the offset")
            print(len(i))
            #if there is more than one packet mark them so they can be re-combined later
            if count < sm_p_length-1:
                more_frag = 1
            else:
                more_frag = 0
            #if this is the first packet then there is no offset
            if count == 0:
                print("this is the more_frag bit when count == 0 ")
                print(more_frag)
                p = NetworkPacket(dst_addr, i, id_num, len(i), 0, more_frag)
                self.out_intf_L[0].put(p.to_byte_S())  # send packets always enqueued successfully
                print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))
            #it's not the first packet so set the offset to be the size of the last packet sent
            else:
                print("this is the more_frag bit after count == 0 ")
                print(more_frag)
                p = NetworkPacket(dst_addr, i, id_num, len(i), (len(i) + len(sm_p[count-1])), more_frag)
                print("this is the length of p")
                print(len(str(p)))
                self.out_intf_L[0].put(p.to_byte_S())  # send packets always enqueued successfully
                print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            print('%s: received packet "%s" on the in interface' % (self, pkt_S))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print(threading.currentThread().getName() + ': Ending')
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

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                    # HERE you will need to implement a lookup into the 
                    # forwarding table to find the appropriate outgoing interface
                    # for now we assume the outgoing interface is also i
                    self.out_intf_L[i].put(p.to_byte_S(), True)
                    print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                        % (self, p, i, i, self.out_intf_L[i].mtu))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print(threading.currentThread().getName() + ': Ending')
                return