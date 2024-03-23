from rpc import *
from cache import *
from database import*
import hashlib
import time
from logger import *
import sys
from config import*
# block={'capabilities': ['proposal'], 'version': 536870912, 'rules': ['csv', '!segwit', 'testdummy', 'taproot'], 'vbavailable': {}, 'vbrequired': 0, 'previousblockhash': '000002ed201a1c5e0b190ff66cd76b703c1168cce29669b45f2d84e03885943b', 'transactions': [], 'coinbaseaux': {}, 'coinbasevalue': 5000000000, 'longpollid': '000002ed201a1c5e0b190ff66cd76b703c1168cce29669b45f2d84e03885943b2019', 'target': '000009debb000000000000000000000000000000000000000000000000000000', 'mintime': 1709116475, 'mutable': ['time', 'transactions', 'prevblock'], 'noncerange': '00000000ffffffff', 'sigoplimit': 80000, 'sizelimit': 4000000, 'weightlimit': 4000000, 'curtime': 1709275188, 'bits': '1e09debb', 'height': 2018, 'default_witness_commitment': '6a24aa21a9ede2f61c3f71d1defd3fa999dfa36953755c690689799962b48bebd836974e8cf9'}

def create_jobs(username,job_id,target,block):
    data={}
    #each miner allowed to use nonce and time for hashing, the difference among them is 
    #each job will have a particular coinbase_scripts, this scripts can be their username or id
    user_scripts=username+str(job_id)
    scripts=hashlib.sha256(user_scripts.encode('utf-8')).hexdigest()
    coinbase=tx_make_coinbase(scripts, pool_address, block["coinbasevalue"], block["height"])
    coinbase_hash=tx_compute_hash(coinbase)
    block["coinbase_data"]=coinbase
    block["transactions"].insert(0,coinbase_hash)
    block["merkleroot"]=tx_compute_merkle_root(block['transactions'])
    block["job_id"]=job_id
    block["start"]=time.time()
    block["target"]=target
    # res=job_id.to_bytes(4,byteorder="big").hex()+version.to_bytes(4,byteorder="big").hex()+prevhash+block["bits"]+block["curtime"].to_bytes(4,byteorder="big").hex()+block["mintime"].to_bytes(4,byteorder="big").hex()+block["merkleroot"]
    return block
def validate_shares(block):
    if block is None:
        return None
    
    status,res=check_block(block)
    return status,res
    

def submit_to_node(block):
    # block_cache=read_block()
    # block_cache=ast.literal_eval(block_cache)
    # block["transactions"]=block_cache["transactions"]
    submission = block_make_submit(block)
    logger=Logger()

    # print("Submitting:",)
    try:
        response = rpc_submitblock(submission)
        if response is not None:
            logger.log_info("Submission Error: {}".format(response))
            # print("Submission Error: {}".format(response))
            return 0
        else:
            # print(response)
            
            return 1
    except:
        logger=Logger()
        logger.log_critical("Bitcoin down")
        sys.exit(0)