from authorize import *
from database import *
from frame import *
from type_message import *
from pool import *
from datetime import datetime
from cache import *
from config import*
from mining import *
import time
from rpc import*
import ast
import hashlib
from logger import *
from config import *
# def register(data):
#     database=Database()
#     byte_data = bytes.fromhex(data.decode('utf-8'))
#     result_string = byte_data.decode('utf-8')
#     auth=Authorize.extract(result_string)
#     miner=database.find_one(Miner, username=auth.username)
#     if (miner):
#         frame=Frame(exist_user,0,"")
#         return frame.create_frame()
#     mock=Miner(id=hashlib.sha256(auth.username+str(datetime.now())),username=auth.username,password=auth.password,address=auth.address,target=DEFAUTL_TARGET)
#     database.add_data(mock)
def open_handler(data,socket):
    database=Database()
    byte_data = bytes.fromhex(data.decode('utf-8'))
    result_string = byte_data.decode('utf-8')
    auth=Authorize.extract(result_string)
    miner=database.find_one(Miner, username=auth.username)
    logger=Logger()

    if miner is None:
        payload=unknown_user
        frame=Frame(open_error,1,str(payload))
        return frame.create_frame()
    #cache data
    if miner.password==auth.password and miner.username==auth.username:
        job=database.find_one(JobRecord,order_by_column="job_id",descending=True,user_id=miner.user_id)
        if (job is None):
            #username can be the token
            user_cache.add_connection(miner.username,socket,None,miner.user_id,miner.target,None)
        else:
            user_cache.add_connection(miner.username,socket,job.job_id,miner.user_id,miner.target,ast.literal_eval(job.block))
        payload=Frame.string_to_hex(miner.target+miner.username)
        frame=Frame(open_success,len(payload),payload)
        res=frame.create_frame()
        return res
    else:
        return None
def request_job_handler(data):
    #receive the new jobs request from miner and return new job
    # job_id=int(data[0:8].decode('utf-8'),16)
    byte_data = bytes.fromhex(data.decode('utf-8'))
    result_string = byte_data.decode('utf-8')
    miner=user_cache.get_connection(result_string)
    database=Database()
    if miner is None:
        payload=unauthorize
        frame=Frame(request_job_error,1,str(payload))
        return frame.create_frame()
    block=read_block()
    block=ast.literal_eval(block)
    if (block is None):
        print("Cannot connect to BtcCore")
        return None
    miner["block"]=block
    current_job=miner["job_id"]
    job=None
    
    if (current_job is None):
        job_id=1
        job=create_jobs(result_string,job_id,miner["target"],miner["block"])
    else:
        job_id=current_job+1
        job=create_jobs(result_string,job_id,miner["target"],miner["block"])
    # if (job is None):
    job_record=JobRecord(user_id=miner["user_id"],job_id=job_id,block=str(job))
    miner["job_id"]=job_id
    miner["block"]=job
    user_cache.update_connection(result_string,miner)
    database.add_data(job_record)
    res=job["job_id"].to_bytes(4,byteorder="big").hex()+job["version"].to_bytes(4,byteorder="big").hex()+job["previousblockhash"]+job["bits"]+job["curtime"].to_bytes(4,byteorder="big").hex()+job["mintime"].to_bytes(4,byteorder="big").hex()+job["merkleroot"]+job["target"]
    frame=Frame(notify_job,len(res),res)
    return frame.create_frame()

def submit_handler(data):
    #validating the block
    logger=Logger()
    job_id=int(data[:8].decode('utf-8'),16)
    nonce=int(data[8:16].decode('utf-8'),16)
    n_time=int(data[16:24].decode('utf-8'),16)
    hashrate=int(data[24:32].decode('utf-8'),16)
    byte_data = bytes.fromhex(data[32:].decode('utf-8'))
    username=byte_data.decode('utf-8')
    miner=user_cache.get_connection(username)
    target=miner["target"]
    miner["block"]["nonce"]=nonce
    miner["block"]["hashrate"]=hashrate
    miner["block"]["curtime"]=n_time
    if (job_id>miner["job_id"]):
        frame=Frame(job_not_found,0,"")
        return frame.create_frame()
    if (job_id<miner["job_id"]):
        frame=Frame(job_is_old,0,"")
        return frame.create_frame()
    status,res=validate_shares(miner["block"])
    if status!=0:
        database=Database()
        miner["block"]=res
        if (status==1):
            if submit_to_node(miner["block"])==0:
                logger.log_info(f"Miner {username} fail to submit to node ")
                frame=Frame(submit_error,0,"")
                return frame.create_frame()
            else:
                logger.log_info(f"Miner {username} submited to node , Block { miner['block']['height'] }")
                r=Reward(reward_id=miner["block"]["transactions"][0],block=miner["block"]["hash"])
                database.add_data(r)

        # hashrate=miner["block"]["hashrate"]
        t=ShareRecord(share_id=miner["block"]["hash"],user_id=miner["user_id"],difficulty=miner["block"]["target"],target_network=miner["block"]["bits"],datetime=datetime.now(),height=miner["block"]["height"],job_id=miner["block"]["job_id"])
        database.add_data(t)
        database.custom_query(f"update miners set hashrate='{hashrate}' where username='{username}';")
        user_cache.update_connection(username,miner)
        frame=Frame(submit_success,0,"")
        return frame.create_frame()
    else:
        frame=Frame(submit_error,1,str(res))
        return frame.create_frame()
def broadcast_block():
    # print("broadcast block")
    logger=Logger()
    logger.log_info("Broadcast block to entire network")
    data=user_cache.get_all_connections()
    for client in data:
        try:
            frame = Frame(set_block, 0, "")
            sock = client[1]["socket"]
            sock.sendall(frame.create_frame())
        except Exception as e:
            logger.log_info(f"Error sending block to client: {e}")
def int_to_32byte_hex(num):
    hex_string = hex(int(num))[2:]  # Convert integer to hexadecimal string
    padded_hex = hex_string.zfill(64)  # Pad with zeros to ensure 32 bytes (64 characters)
    return padded_hex

def update_target(start,end):
    logger=Logger()
    try:
        logger.log_info("Update miner's target")
        database=Database()
        miners=database.custom_query(f"select miners.target,miners.username,miners.hashrate,count(share_record.share_id) from miners,share_record where miners.user_id=share_record.user_id and share_record.height>= {start} and share_record.height<={end} group by miners.user_id")
        data=user_cache.get_all_connections()
        for miner in miners:
            new_target=0
            print(miner[2])
            d=(miner[2]*2)/pow(2,8)
            int_target=(int((DEFAUTL_TARGET),16))
            new_target=int_target/int(d)
            new_target=int_to_32byte_hex(new_target)
            print(new_target)

            database.custom_query(f"update miners set target='{new_target}' where username='{miner[1]}';")
            for client in data:
                if client[0]==miner[1]:
                    client[1]["target"]=new_target
                    user_cache.update_connection(miner[1],client[1])
    except e:
        logger.log_critical(e)

#bcrt1qca54pw9pzqdlz5fm4wm8ml6qa4q5vp5qjekt2a
# update_target(2025,2027)
# t=time.time()
# time.sleep(10)
# t1=time.time()
# print(t1-t)
# Example usage
# integer_value = 9305245895680597045479230516168994599843208932407817362870921237171798016
# hex_representation = int_to_32byte_hex(int(integer_value))
# print(hex_representation)
        


