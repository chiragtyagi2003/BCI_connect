import os
from dotenv import load_dotenv
from websocket import create_connection
import json
from time import sleep
import firebase_admin
from firebase_admin import credentials, db

load_dotenv()

clientId = os.getenv("clientId")
clientSecret = os.getenv("clientSecret")
print("clientId: ", clientId)
print("clientSecret: ", clientSecret)
firebaseDatabaseUrl = os.getenv("firebaseDatabaseUrl")

# # database connection
cred = credentials.Certificate("credentials.json")
firebase_admin.initialize_app(cred, {"databaseURL": firebaseDatabaseUrl})
ref = db.reference("/")

# websocket connection
ws = create_connection("wss://localhost:6868")


def send_message(j):
    j = json.dumps(j)
    ws.send(j)
    response = ws.recv()
    return (response)

# do this reqeust access only the very frist time
# getCortexToken = send_message({
#         "id": 3,
#         "jsonrpc": "2.0",
#         "method": "requestAccess",
#         "params": {
#             "clientId": clientId,
#             "clientSecret": clientSecret
#         }
#     })

getCortexToken = send_message({
        "id": 1,
        "jsonrpc": "2.0",
        "method": "authorize",
        "params": {
            "clientId": clientId,
            "clientSecret": clientSecret
        }
    })
getCortexToken = json.loads(getCortexToken)
# print(getCortexToken)
cortexToken = getCortexToken["result"]["cortexToken"]

createSession = send_message({
    "id": 1,
    "jsonrpc": "2.0",
    "method": "createSession",
    "params": {
        "cortexToken": cortexToken,
        "headset": "EPOCX-E5020501",
        "status": "open"
    }
})

createSession = json.loads(createSession)

try:
    sessionId = createSession['result']['id']
except Exception as e:
    print(str(e))
    print("Enable to connect to headset")
    exit(1)

load_profile = send_message({
    "id": 1,
    "jsonrpc": "2.0",
    "method": "setupProfile",
    "params": {
        "cortexToken": cortexToken,
        "headset": "EPOCX-E5020501",
        "profile": "chiragtyagi",
        "status": "load"
    }
})

subscribe = send_message({
    "id": 1,
    "jsonrpc": "2.0",
    "method": "subscribe",
    "params": {
        "cortexToken": cortexToken,
        "session": sessionId,
        "streams": ["com"]  # "fac"
    }
})

# # available actions - 
# # com stream - push, pull, lift, drop
# # fac stream - smile, furrow brows, clench teeth, raise brows, wink left, wink right

ws.recv()
subscribe = json.loads(subscribe)
print(subscribe)

print( "Sent")
print( "Receiving...")


result = ws.recv()
result = json.loads(result)
# print(result)

flag = False
prev_action = ""

while True:
    result = ws.recv()
    result = json.loads(result)

    
    if "com" in result:
        action = result["com"][0]
        power = result["com"][1]

        if action == "left" and power >= 0.5:
            flag = True
            prev_action = "com"
            db.reference("/left").set({"enabled": True})
            db.reference("/right").set({"enabled": False})
            db.reference("/neutral").set({"enabled": False})
            print("Received ", result)

        elif action == "right" and power >= 0.5:
            flag = True
            prev_action = "com"
            db.reference("/right").set({"enabled": True})
            db.reference("/neutral").set({"enabled": False})
            db.reference("/left").set({"enabled": False})
            print("Received ", result)

        elif action == "neutral" and power >= 0.5:
            flag = True
            prev_action = "com"
            db.reference("/neutral").set({"enabled": True})
            db.reference("/left").set({"enabled": False})
            db.reference("/right").set({"enabled": False})
            print("Received ", result)
            
    if flag == True:
        sleep(10)
        flag = False


ws.close