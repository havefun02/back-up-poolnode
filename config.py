import configparser
config = configparser.ConfigParser()
config.read('config.ini')

RPC_URL=config['bitcoin']['RPC_URL']
RPC_URL_WALLET=config['bitcoin']['RPC_URL_WALLET']
RPC_USER=config['bitcoin']['RPC_USER']
RPC_PASS=config['bitcoin']['RPC_PASS']
DEFAUTL_TARGET=config['pool']['DEFAUTL_TARGET']
POOL_FEE=config['pool']['POOL_FEE']
REWARD_TIME=config['pool']['REWARD_TIME']
UPDATE_TARGET=config['pool']['UPDATE_TARGET']
SERVER=config['pool']['SERVER']
PORT=config['pool']['PORT']
HTTP_SERVER=config['pool']['HTTP_SERVER']
HTTP_PORT=config['pool']['HTTP_PORT']
STATISTIC_IP=config['pool']['STATISTIC_IP']
STATISTIC_PORT=config['pool']['STATISTIC_PORT']
POOL_ADDRESS=config['pool']['POOL_ADDRESS']
