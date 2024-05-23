class Authorize:
    def __init__(self,username,password,address=None):
        self.username=username
        self.password=password
        self.address=address
    def createString(self):
        if (self.address is None):
            return self.username+ ":" + self.password
        else:
            return self.username+ ":" + self.password+":"+self.address
    def extract(credentials_string):
        data = credentials_string.split(":")
        if (len(data)==2):
            return Authorize(data[0],data[1])
        elif (len(data)==3):
            return Authorize(data[0],data[1],data[2])
