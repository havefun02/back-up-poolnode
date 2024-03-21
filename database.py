from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime,text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

Base = declarative_base()

class Miner(Base):
    __tablename__ = 'miners'
    id = Column(String, primary_key=True)
    username = Column(String, primary_key=True)
    password=Column(String,nullable=False)
    address = Column(String, nullable=False)
    hashrate = Column(String, nullable=True)
    target = Column(String, nullable=False)

class ShareRecord(Base):
    __tablename__ = 'share_record'
    id = Column(String, primary_key=True)
    id_user = Column(String, ForeignKey('miners.id'), primary_key=True)
    difficulty = Column(String, nullable=False)
    target_network = Column(String, nullable=False)
    datetime = Column(DateTime, nullable=False)
    duration=Column(Integer,nullable=False)
    hashrate= Column(String, nullable=False)
    job_id = Column(Integer, nullable=False)
    height=Column(Integer, nullable=False)
class JobRecord(Base):
    __tablename__ = 'jobs_record'
    id_user = Column(String, ForeignKey('miners.id'), primary_key=True)
    job_id = Column(Integer, primary_key=True)
    block = Column(Text, nullable=False)
class Reward(Base):
    __tablename__ = 'reward_record'
    id=Column(String, primary_key=True)
    block = Column(String, primary_key=False)
    # btc=Column(Integer, nullable=False)


class Database:
    _instance = None  # Class variable to store the singleton instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, database_url='sqlite:///pool.db'):
        if self._initialized:
            return
        self._initialized = True

        self.engine = create_engine(database_url, echo=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_instance(self):
        session = self.Session()
        return session

    def create_all_entities(self, drop_existing=False):
        if drop_existing:
            Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        session = self.get_instance()
        try:
            session.commit()
        finally:
            session.close()

    def add_data(self, data):
        session = self.get_instance()
        try:
            session.add(data)
            session.commit()
        finally:
            session.close()

    def update_data(self, data):
        session = self.get_instance()
        try:
            session.merge(data)
            session.commit()
        finally:
            session.close()
    def custom_query(self,query):
        session = self.get_instance()
        try:
            result = session.execute(text(query))
            session.commit()  # Commit the transaction
            return result.fetchall()
        except SQLAlchemyError as e:
            print("Error executing query:", e)
            return None




    def find_one(self, model, order_by_column=None, descending=False, **kwargs):
        session = self.get_instance()
        try:
            query = session.query(model).filter_by(**kwargs)
            
            # Add ordering if a column is specified
            if order_by_column:
                order_by_attribute = getattr(model, str(order_by_column))
                if descending:
                    order_by_attribute = order_by_attribute.desc()
                query = query.order_by(order_by_attribute)
            
            result = query.first()
            return result
        finally:
            session.close()

    def find_all(self, model, **kwargs):
        session = self.get_instance()
        try:
            result = session.query(model).filter_by(**kwargs).all()
            if (result):
                return result
            return None
        finally:
            session.close()

# database=Database()
# database.create_all_entities(drop_existing=True)
# miner = Miner(id='123', username='username', password='password', address='bcrt1qgwev460zqprwlvnv45nq3tyuwgj4t8ukx8qs53',hashrate=None,target="000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")
# miner = Miner(id='1234', username='username1', password='password', address='bcrt1qgwev460zqprwlvnv45nq3tyuwgj4t8ukx8qs53',hashrate=None,target="000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")
# database.add_data(miner)