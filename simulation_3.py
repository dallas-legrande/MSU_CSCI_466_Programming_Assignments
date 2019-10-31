'''
    Chris Cooper and Dallas LeGrande
    CSCI 466
    Assignment 3
'''

import network_3
import link_3
import threading
from time import sleep

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 5 #give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads

    #create network nodes
    client_1 = network_3.Host(1)
    object_L.append(client_1)
    client_2 = network_3.Host(2)
    object_L.append(client_2)
    server_3 = network_3.Host(3)
    object_L.append(server_3)
    server_4 = network_3.Host(4)
    object_L.append(server_4)
    router_a = network_3.Router(name='A', intf_count=2, max_queue_size=router_queue_size)
    object_L.append(router_a)
    router_b = network_3.Router(name='B', intf_count=1, max_queue_size=router_queue_size)
    object_L.append(router_a)
    router_c = network_3.Router(name='C', intf_count=1, max_queue_size=router_queue_size)
    object_L.append(router_a)
    router_d = network_3.Router(name='D', intf_count=2, max_queue_size=router_queue_size)
    object_L.append(router_a)

    #create a Link Layer to keep track of links between network nodes
    link_layer = link_3.LinkLayer()
    object_L.append(link_layer)

    #add all the links
    #link parameters: from_node, from_intf_num, to_node, to_intf_num, mtu
    link_layer.add_link(link_3.Link(client_1, 0, router_a, 0, 50))
    link_layer.add_link(link_3.Link(router_a, 0, router_b, 0, 30))
    link_layer.add_link(link_3.Link(router_b, 0, router_d, 0, 30))
    link_layer.add_link(link_3.Link(router_d, 0, server_3, 0, 30))

    link_layer.add_link(link_3.Link(client_2, 0, router_a, 1, 50))
    link_layer.add_link(link_3.Link(router_a, 1, router_c, 0, 30))
    link_layer.add_link(link_3.Link(router_c, 0, router_d, 1, 30))
    link_layer.add_link(link_3.Link(router_d, 1, server_4, 0, 30))

    #start all the objects
    thread_L = []
    thread_L.append(threading.Thread(name=client_1.__str__(), target=client_1.run))
    thread_L.append(threading.Thread(name=client_2.__str__(), target=client_2.run))

    thread_L.append(threading.Thread(name=server_3.__str__(), target=server_3.run))
    thread_L.append(threading.Thread(name=server_4.__str__(), target=server_4.run))

    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(name=router_d.__str__(), target=router_d.run))

    thread_L.append(threading.Thread(name="Network", target=link_layer.run))

    for t in thread_L:
        t.start()

    # send 80 character message to host with address 3
    message = "Let us not, dear friends, forget our dear friends the cuttlefish... flipper conories little sausages. "
    client_1.udt_send(3, message)

    # send 70 character message to host with address 4
    message2 = "I submit here and now, that is what we all must do- we must fight... to run away."
    client_2.udt_send(4, message2)

    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)

    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()

    print("All simulation threads joined")
