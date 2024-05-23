from network import*
from config import *
from database import *
def __main__():
    database=Database()
    database.create_all_entities(drop_existing=False)
    mining_server = MiningServer(str(SERVER),int(PORT))
    mining_server.start_server()
__main__()