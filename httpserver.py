from flask import Flask, jsonify
from config import *
from database import *
from rpc import block_bits2target
app = Flask(__name__)
database=Database()


# API endpoint to get the data

def toJsonShareData(data):
    target=block_bits2target(data.target_network)
    return {"id":data.id,"share":data.difficulty,"target":str(target.hex()),"datetime":data.datetime}
@app.route('/api/data/<int:user_id>', methods=['GET'])
def get_data(user_id):
    user_data=database.find_one(Miner,id=user_id)
    if user_data:    
        data_shares=database.find_all(ShareRecord,id_user=user_id)
        data_list = [toJsonShareData(record) for record in data_shares]

    return jsonify({"data":data_list })

if __name__ == '__main__':
    app.run(debug=True, host=HTTP_SERVER, port=int(HTTP_PORT))
