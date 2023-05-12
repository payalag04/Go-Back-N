from typing import BinaryIO
import binascii
import socket
import struct 
import os

buffsize=256
length_window=60

def gbn_server(iface:str, port:int, fp:BinaryIO) -> None:
    print("Hello, I am a server")
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # addrs is a combination of iface and port value that is to be sent to the bind function using getaddrinfo()
    ack_server = -1
    addrs = socket.getaddrinfo(iface, port)
    udp_server.bind(addrs[0][-1])
    ack_exp = 0
    while True:
        data_received ,addr = udp_server.recvfrom(buffsize+(struct.calcsize('QQ?')))
        i, checksum, end = struct.unpack('QQ?', data_received[:(struct.calcsize('QQ?'))])
        data = data_received[struct.calcsize('QQ?'):]
        if i <= ack_exp:
            if i == ack_exp:
                fp.write(data)
                ack_exp = i + 1
            udp_server.sendto(struct.pack('?Q',True,i), addr)
            if end:
                return
        else:
            udp_server.sendto(struct.pack('?Q',False,ack_exp), addr)

def gbn_client(host:str, port:int, fp:BinaryIO) -> None:
    print("Hello, I am a client")
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_client.connect((host, port))
    i=0
    window_list=[]
    fp.seek(0,os.SEEK_END)
    end_pos = fp.tell()
    fp.seek(0)
    while True:
        while fp.tell() != end_pos:
            if len(window_list)< length_window:
                message = fp.read(buffsize)
                window_list.append((i,message))
                data_to_send = struct.pack('QQ?',i, binascii.crc32(message), message ==b'') + message
                udp_client.send(data_to_send)
                i+=1
            
            if len(window_list)==length_window:
                try:
                    data_received = udp_client.recv(struct.calcsize('?Q'))
                    ack, j = struct.unpack('?Q', data_received)    
                except socket.timeout:
                    for sequence, message in window_list:
                        data_to_send=struct.pack('QQ?',sequence, binascii.crc32(message), message ==b'') + message
                        udp_client.send(data_to_send)
                if not ack:
                    for sequence, message in window_list:
                        data_to_send=stryct.pack('QQ?',sequence, binascii.crc32(message), message ==b'') + message
                        udp_client.send(data_to_send)
                elif ack:
                    while window_list[0][0]<=j:
                        window_list.pop(0)   
        if len(window_list) !=0:
            for sequence, message in window_list:
                data_to_send=struct.pack('QQ?',sequence, binascii.crc32(message), message ==b'') + message
                udp_client.send(data_to_send)

        while len(window_list)!=0:                                                                       
            try:
                data_received = udp_client.recv(struct.calcsize('?Q'))
                ack, j = struct.unpack('?Q', data_received)   
            except socket.timeout:
                for sequence, message in window_list:
                    data_to_send=struct.pack('QQ?',sequence, binascii.crc32(message), message ==b'')   + message    
                    udp_client.send(data_to_send)
            if not ack or j != window_list[0][0]:
                for sequence, message in window_list:
                    data_to_send=struct.pack('QQ?',sequence, binascii.crc32(message), message==b'' ) + message
                    udp_client.send(data_to_send)
            elif ack and  window_list[0][0]==j:
                window_list.pop(0)           
        message = b''
        data_to_send =  struct.pack('QQ?',j+1, binascii.crc32(message), message ==b'')+message  
        for i in range(10):
            udp_client.send(data_to_send)
        return