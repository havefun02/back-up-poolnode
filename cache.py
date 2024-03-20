from cachetools import LRUCache
from datetime import datetime, timedelta
class UserConnectionCache:
    def __init__(self, maxsize=100):
        self.cache = LRUCache(maxsize=maxsize)

    def add_connection(self, username, socket,job_id,user_id,target,block):
        expire_time = datetime.now() + timedelta(hours=12)
        data = {'socket': socket, 'expire': expire_time,"job_id":job_id,"user_id":user_id,"target":target,"block":block}
        self.cache[username] = data
    def update_connection(self,username,data):
        self.cache[username]=data
    def get_connection(self, username):
        return self.cache.get(username, None)

    def remove_connection(self, username):
        if username in self.cache:
            del self.cache[username]
    def get_all_connections(self):
        return list(self.cache.items())


user_cache = UserConnectionCache(maxsize=100)
