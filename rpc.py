from config import *
import urllib.request
import urllib.error
import urllib.parse
import base64
import json
import hashlib
import struct
import random
import time
import os
import sys
from type_message import *

def check_block(block):
    # Compute the target hash
    target_hash = block_bits2target(block['bits'])
    target_share_hash = bytes.fromhex(block["target"])
    block_header = block_make_header(block)
    block_hash = block_compute_raw_hash(block_header)
    # print(block_hash.hex(),target_share_hash.hex())
    if block_hash < target_hash:
        # print("found block")
        #valid to network target
        block['hash'] = block_hash.hex()
        return (0x01,block)
    if (block_hash<target_share_hash):
        #valid to miner target
        block['hash'] = block_hash.hex()
        return (0x02,block)
    
    return (0x00,low_difficulty_share)


def rpc_base(method, params=None):
    rpc_id = random.getrandbits(32)
    data = json.dumps({"id": rpc_id, "method": method, "params": params}).encode()
    auth = base64.encodebytes((RPC_USER + ":" + RPC_PASS).encode()).decode().strip()

    request = urllib.request.Request(RPC_URL, data, {"Authorization": "Basic {:s}".format(auth)})

    with urllib.request.urlopen(request) as f:
        response = json.loads(f.read())

    if response['id'] != rpc_id:
        raise ValueError("Invalid response id: got {}, expected {:u}".format(response['id'], rpc_id))
    elif response['error'] is not None:
        raise ValueError("RPC error: {:s}".format(json.dumps(response['error'])))

    return response['result']
def rpc_wallet_base(method, params=None):
    rpc_id = random.getrandbits(32)
    data = json.dumps({"id": rpc_id, "method": method, "params": params}).encode()
    auth = base64.encodebytes((RPC_USER + ":" + RPC_PASS).encode()).decode().strip()

    request = urllib.request.Request(RPC_URL_WALLET, data, {"Authorization": "Basic {:s}".format(auth)})

    with urllib.request.urlopen(request) as f:
        response = json.loads(f.read())

    if response['id'] != rpc_id:
        raise ValueError("Invalid response id: got {}, expected {:u}".format(response['id'], rpc_id))
    elif response['error'] is not None:
        raise ValueError("RPC error: {:s}".format(json.dumps(response['error'])))

    return response['result']


def rpc_getblocktemplate(longid):
    try:
       # return rpc("getblocktemplate", [{"rules": ["segwit"],"capabilities":["longpoll"]}])
        if longid is None:
            return rpc_base("getblocktemplate", [{"rules": ["segwit"]}])
        else:
            return rpc_base("getblocktemplate", [{"rules": ["segwit"],"longpollid":longid}])
    except ValueError:
        return {}
def rpc_submitblock(block_submission):
    return rpc_base("submitblock", [block_submission])
def rpc_gettxn(txn,block):
    return rpc_base("getrawtransaction",[txn,True,block])
def rpc_getwallet():
    return rpc_wallet_base("getwalletinfo")

def int2lehex(value, width):
    """
    Convert an unsigned integer to a little endian ASCII hex string.

    Args:
        value (int): value
        width (int): byte width

    Returns:
        string: ASCII hex string
    """

    return value.to_bytes(width, byteorder='little').hex()


def int2varinthex(value):
    """
    Convert an unsigned integer to little endian varint ASCII hex string.

    Args:
        value (int): value

    Returns:
        string: ASCII hex string
    """

    if value < 0xfd:
        return int2lehex(value, 1)
    elif value <= 0xffff:
        return "fd" + int2lehex(value, 2)
    elif value <= 0xffffffff:
        return "fe" + int2lehex(value, 4)
    else:
        return "ff" + int2lehex(value, 8)


def bitcoinaddress2hash160(addr):
    """
    Convert a Base58 Bitcoin address to its Hash-160 ASCII hex string.

    Args:
        addr (string): Base58 Bitcoin address

    Returns:
        string: Hash-160 ASCII hex string
    """

    table = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    hash160 = 0
    addr = addr[::-1]
    for i, c in enumerate(addr):
        hash160 += (58 ** i) * table.find(c)

    # Convert number to 50-byte ASCII Hex string
    hash160 = "{:050x}".format(hash160)

    # Discard 1-byte network byte at beginning and 4-byte checksum at the end
    return hash160[2:50 - 8]


################################################################################
# Transaction Coinbase and Hashing Functions
################################################################################


def tx_encode_coinbase_height(height):
    """
    Encode the coinbase height, as per BIP 34:
    https://github.com/bitcoin/bips/blob/master/bip-0034.mediawiki

    Arguments:
        height (int): height of the mined block

    Returns:
        string: encoded height as an ASCII hex string
    """

    width = (height.bit_length() + 7) // 8

    return bytes([width]).hex() + int2lehex(height, width)

import bech32
# address = "bcrt1q5gc3pcj534qq8xatpvz3y4wg706ecdsq9vnkj7"
# res=bech32.decode("bcrt",address)
def create_script_pubkey(witness_version, byte_data):
    if witness_version == 0:
        script_pubkey = 0x00.to_bytes(1,byteorder="big") + 0x14.to_bytes(1,byteorder="big") + bytes(byte_data)
        script_pubkey_hex = script_pubkey.hex()
        return script_pubkey_hex
    else:
        return "Unsupported witness version"


def tx_make_coinbase(coinbase_script, address, value, height):
    """
    Create a coinbase transaction.

    Arguments:
        coinbase_script (string): arbitrary script as an ASCII hex string
        address (string): Base58 Bitcoin address
        value (int): coinbase value
        height (int): mined block height

    Returns:
        string: coinbase transaction as an ASCII hex string
    """

    # See https://en.bitcoin.it/wiki/Transaction

    coinbase_script = tx_encode_coinbase_height(height) + coinbase_script

    # Create a pubkey script
    # OP_DUP OP_HASH160 <len to push> <pubkey> OP_EQUALVERIFY OP_CHECKSIG
    # pubkey_script = "76" + "a9" + "14" + bitcoinaddress2hash160(address) + "88" + "ac"
    res=bech32.decode("bcrt",address)
    pubkey_script=create_script_pubkey(res[0],res[1])
    tx = ""
    # version
    tx += "01000000"
    # in-counter
    tx += "01"
    # input[0] prev hash
    tx += "0" * 64
    # input[0] prev seqnum
    tx += "ffffffff"
    # input[0] script len
    tx += int2varinthex(len(coinbase_script) // 2)
    # input[0] script
    tx += coinbase_script
    # input[0] seqnum
    tx += "ffffffff"
    # out-counter
    tx += "01"
    # output[0] value
    tx += int2lehex(value, 8)
    # output[0] script len
    tx += int2varinthex(len(pubkey_script) // 2)
    # output[0] script
    tx += pubkey_script
    # lock-time
    tx += "00000000"

    return tx


def tx_compute_hash(tx):
    """
    Compute the SHA256 double hash of a transaction.

    Arguments:
        tx (string): transaction data as an ASCII hex string

    Return:
        string: transaction hash as an ASCII hex string
    """

    return hashlib.sha256(hashlib.sha256(bytes.fromhex(tx)).digest()).digest()[::-1].hex()


def tx_compute_merkle_root(tx_hashes):
    """
    Compute the Merkle Root of a list of transaction hashes.

    Arguments:
        tx_hashes (list): list of transaction hashes as ASCII hex strings

    Returns:
        string: merkle root as a big endian ASCII hex string
    """

    # Convert list of ASCII hex transaction hashes into bytes

    tx_hashes = [bytes.fromhex(tx_hash)[::-1] for tx_hash in tx_hashes]

    # Iteratively compute the merkle root hash
    while len(tx_hashes) > 1:
        # Duplicate last hash if the list is odd
        if len(tx_hashes) % 2 != 0:
            tx_hashes.append(tx_hashes[-1])

        tx_hashes_new = []

        for i in range(len(tx_hashes) // 2):
            # Concatenate the next two
            concat = tx_hashes.pop(0) + tx_hashes.pop(0)
            # Hash them
            concat_hash = hashlib.sha256(hashlib.sha256(concat).digest()).digest()
            # Add them to our working list
            tx_hashes_new.append(concat_hash)

        tx_hashes = tx_hashes_new

    # Format the root in big endian ascii hex
    return tx_hashes[0][::-1].hex()


################################################################################
# Block Preparation Functions
################################################################################


def block_make_header(block):
    """
    Make the block header.

    Arguments:
        block (dict): block template

    Returns:
        bytes: block header
    """
    header = b""

    # Version
    header += struct.pack("<L", block['version'])
    # Previous Block Hash
    header += bytes.fromhex(block['previousblockhash'])[::-1]
    # Merkle Root Hash
    header += bytes.fromhex(block['merkleroot'])[::-1]
    # Time
    header += struct.pack("<L", block['curtime'])
    # Target Bits
    header += bytes.fromhex(block['bits'])[::-1]
    # Nonce
    header += struct.pack("<L", block['nonce'])

    return header


def block_compute_raw_hash(header):
    """
    Compute the raw SHA256 double hash of a block header.

    Arguments:
        header (bytes): block header

    Returns:
        bytes: block hash
    """

    return hashlib.sha256(hashlib.sha256(header).digest()).digest()[::-1]


def block_bits2target(bits):
    """
    Convert compressed target (block bits) encoding to target value.

    Arguments:
        bits (string): compressed target as an ASCII hex string

    Returns:
        bytes: big endian target
    """

    # Bits: 1b0404cb
    #       1b          left shift of (0x1b - 3) bytes
    #         0404cb    value
    bits = bytes.fromhex(bits)
    shift = bits[0] - 3
    value = bits[1:]

    # Shift value to the left by shift
    target = value + b"\x00" * shift
    # Add leading zeros
    target = b"\x00" * (32 - len(target)) + target

    return target


def block_make_submit(block):

    submission = ""
    # Block header
    submission += block_make_header(block).hex()
    # Number of transactions as a varint
    submission += int2varinthex(len(block['transactions']))
    # Concatenated transactions data
    submission+=block['coinbase_data']
    # for tx in block['transactions']:
        # submission += tx

    return submission

