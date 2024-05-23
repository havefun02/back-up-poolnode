import socket
import selectors
import types
import struct
import signal
from type_message import *
from frame import *
import time  # Add this import for the 'time' module
from protocols import open_handler,submit_handler,request_job_handler,broadcast_block,update_target
from rpc import *
from cache import *
from config import *
import threading  # Import the threading module
from logger import *
from mining import *
import ast
import sys
from type_message import *
from frame import *
from protocols import open_handler, submit_handler, request_job_handler, broadcast_block,update_target
from rpc import *
from cache import *
from config import *
import threading
from logger import *
from mining import *

class MiningServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sel = selectors.DefaultSelector()
        self.server_sock = None
        # self.block_data_lock = threading.Lock()
        self.old_block=None
        self.new_block_data = None
        self.longid = None
        self.logger = Logger()

    def get_state(self):
        return self.state

    def handle_termination(self, signum, frame):
        self.logger.log_critical("Server terminated. Closing connections.")
        # print("Server terminated. Closing connections.")
        self.server_sock.close()
        sys.exit(0)

    def perform_handshake(self,client_socket):
        # Send the handshake message
        frame=Frame(hello,0,"")
        client_socket.sendall(frame.create_frame())

        # Receive the response from the client
        response = client_socket.recv(1024)
        response=Frame.extract_frame(response)
        if int.from_bytes(response.type,byteorder="little") == ack_hello:
            frame=Frame(hello_ok,0,"")
            client_socket.sendall(frame.create_frame())
            # print("Handshake successful")
            return 1
        else:
            # print("Handshake failed")
            return 0

    def send_data(self,client_socket, data):
        client_socket.sendall(data)

    def start_server(self):
        # sel = selectors.DefaultSelector()

        # global server_sock
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        server_sock.listen()

        self.logger.log_info(f"Server listening on {self.host}:{self.port}")
        signal.signal(signal.SIGINT, self.handle_termination)

        server_sock.setblocking(False)
        self.sel.register(server_sock, selectors.EVENT_READ, data=None)

        block_thread = threading.Thread(target=self.receive_new_blocks)
        block_thread.start()

        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        finally:
            self.sel.close()

    def accept_wrapper(self,sock):
        conn, addr = sock.accept()
        if self.perform_handshake(conn)==0:
            return None
        self.logger.log_info(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)
    def service_connection(self,key, mask):
        sock = key.fileobj
        data = key.data
        try:
            if mask & selectors.EVENT_READ:
                recv_data = sock.recv(1024)
                if recv_data:
                    # data.outb += recv_data
                    frame_extraction=Frame.extract_frame(recv_data)
                    self.forward_to_method(frame_extraction.type,frame_extraction.payload,sock)
                else:
                    self.logger.log_info(f"Closing connection to {data.addr}")
                    self.sel.unregister(sock)
                    sock.close()
        except Exception as e:
            self.logger.log_warning(f"An unexpected error occurred: {e}")
        
    def forward_to_method(self,type_method,data,sock):
        if int.from_bytes(type_method,'little') == open_connection:
            res=open_handler(data,sock)
            if (res is not None):
                self.logger.log_info("Miner " + "authorized")
            self.send_data(sock,res)
        # elif int.from_bytes(type_method,'little')==register:
        #     self.logger.log_info("Miner " + " register")
        #     res=register(data)
        #     self.send_data(sock,res)
        elif int.from_bytes(type_method,'little') == submit_job:
            # self.logger.log_info("Miner " + " submit block"+str(datetime.now()) )
            response=submit_handler(data)
            self.send_data(sock,response)
        elif int.from_bytes(type_method,'little') == request_job:
            self.logger.log_info("Miner " + "request job")
            res=request_job_handler(data)
            self.send_data(sock,res)
        # elif int.from_bytes(type_method,'little') == request_target:
        #     self.logger.log_info("Miner " + " request target")
        #     res=set_target_handler(data)
        #     self.send_data(sock,res)
        else:
            self.logger.log_critical("Unknow message")
            # print(f"Unknown message type: {type_method}")
    def receive_new_blocks(self):
        tmp=read_block()
        if tmp is not None:
            self.old_block=ast.literal_eval(tmp)            
        block=None
        tmp=0
        while True:
            if self.longid!=tmp:
                try:
                    tmp=self.longid
                    block=rpc_getblocktemplate(self.longid)
                    # self.logger.log_info("Get block")

                except:
                    self.logger.log_critical("Cannot get block, Bitcoin down")
            
            if (block is not None):
                if (self.new_block_data is not None):
                    if (block["height"]==self.new_block_data["height"]):
                        continue
                self.logger.log_info(f"Get new block:{block['height']}")
                if self.longid==block["longpollid"]:
                    block=None
                    continue
                else:
                    self.longid=block["longpollid"]
                self.new_block_data=block
                if self.old_block is None:
                    self.old_block=self.new_block_data
                    write_block(self.new_block_data)
                    counter=read_counter()
                    if (counter==None):
                        write_counter(0)
                    if int(str(counter),10)+1>=UPDATE_TARGET:
                        write_counter(0)
                        update_target(block["height"]-UPDATE_TARGET,block["height"]-1)
                    else:
                        write_counter(int(counter,10)+1)

                elif (self.new_block_data["height"]>self.old_block["height"]):
                    self.old_block=self.new_block_data
                    write_block(self.new_block_data)
                    counter=read_counter()
                    if (counter==None):
                        write_counter(0)
                    if int(str(counter))+1>=int(UPDATE_TARGET):
                        write_counter(0)
                        update_target(block["height"]-int(UPDATE_TARGET),block["height"]-1)
                    else:
                        write_counter(int(counter)+1)
                else:
                    self.old_block=self.new_block_data
                    write_block(self.new_block_data)
                broadcast_block()
                block=None

# if __name__ == "__main__":
#     start_server('127.0.0.1', 3000)
