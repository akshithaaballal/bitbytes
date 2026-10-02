#Start of bot code

#BitBytesData
#BitBytesData

import time
import json
import requests
import base64
from datetime import datetime
import calendar
import uuid
from threading import Thread
import queue as Queue
import sys
from sys import platform
import os
from dotenv import load_dotenv

# Load agent environment variables
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_ENV_PATH):
    load_dotenv(_ENV_PATH)

API_BASE = os.getenv('COSMITUDE_API_BASE', 'https://ca.cosmitude.com')
MAC_ADDRESS = os.getenv('COSMITUDE_MAC_ADDRESS', 'Bridge-Web')
USER_NAME = os.getenv('COSMITUDE_USERNAME', '@uuid6e47f42c43ef4fc19054770dca3b2cea')
PASSWORD = os.getenv('COSMITUDE_PASSWORD', 'CosmitudeBridgeDevice')
SERVER_ID = os.getenv('COSMITUDE_SERVER_ID', 'c9b6722d-5dbf-4b4f-a28e-692b4d26c1cf-7870eb8e-2f45-458a-9a70-d6b2d71ee871')
forumID = os.getenv('COSMITUDE_FORUM_ID', '99163d71-96b5-4575-9cf9-8341fb36c917')

Sessionid = ''
username = ''
MobileNumber = ''

def go():
    try:
        login()
        
        while True:
            clienntSync()
            time.sleep(10)
    except Exception as e:
        print (e)
        return e

#------------------------------------------
#Login
#------------------------------------------

def login():
    try:
        global Sessionid
        global username
        global MobileNumber
        global forumID
        tempJson = {
        "MACAddress": MAC_ADDRESS,
        "UserName": USER_NAME,
        "Password": PASSWORD,
        "ServerID": SERVER_ID
        }
        headers = {'Content-Type': 'application/json'}
        variab =json.dumps(tempJson)
        response = requests.post(f'{API_BASE}/loginForDevice', data=variab,headers=headers, timeout=600)
        strData = str(response.text)
        respJson = json.loads(strData)
        Sessionid = respJson['ErrorMessage']['SessionID']
        countryCode = MobileNumber = respJson['ErrorMessage']['CountryCode']
        MobileNumber = countryCode+respJson['ErrorMessage']['MobileNumber']
        getForumDetails()
    except Exception as e:
        print (e)
        return e

#------------------------------------------
#Forum Details
#------------------------------------------ 
def getForumDetails():
    try:
        tempJson = {
        "MACAddress": MAC_ADDRESS,
        "ForumID": forumID,
        "SessionID": Sessionid,
        "ServerID": SERVER_ID
        }
        headers = {'Content-Type': 'application/json'}
        variab =json.dumps(tempJson)
        response = requests.post(f'{API_BASE}/getRequestedForumDetails', data=variab,headers=headers, timeout=600)
        if response.status_code == 200:
            responseStr = str(response.text)
            respJson = json.loads(responseStr)
            errorCode = respJson['ErrorCode']
            if errorCode == 1172:
                errorMsg = respJson['ErrorMessage']
                forumDetails = errorMsg['ForumDataArray']
                for singleForum in forumDetails:
                    singleForumDetails = singleForum[forumID]
                    saveForumDetails = singleForumDetails['NewForumJsonData']
                    admin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'BitBytesData_BitBytesData_Admin.txt')
                    with open(admin_path, 'w') as f:
                        json.dump(saveForumDetails, f)
    except Exception as e:
        print (e)
        return e

#------------------------------------------
#Client Sync
#------------------------------------------

def clienntSync():
    try:
        clientSyncJson = {
        "SessionID": Sessionid,
        "MACAddress": MAC_ADDRESS,
        "ServerID": SERVER_ID,
        "ServerName": 'Bridge'
        }
        headers = {'Content-Type': 'application/json'}
        variab =json.dumps(clientSyncJson)
        response = requests.post(f'{API_BASE}/syncUserData', data=variab,headers=headers, timeout=600)
        strData = str(response.text)
        dataRead = json.loads(strData)
        print(dataRead['ErrorMessage'])
        syncData = dataRead['ErrorMessage']['Admin']
        if syncData.count:
            for data in syncData:
                if 'Bridge' in data:
                    bridgeData = data['Bridge']
                    flowName = bridgeData ['FlowID']
                    mNumber = bridgeData ['MobileNumber']
                    #<YOUR CODE STARTS HERE>
                    if flowName == "BitBytesData_ApplicationModule" and MobileNumber != mNumber:
                        ##Operation2
                        sendData2 = {
            'BitBytesData_ProcessingStages_Main-c88bb07a-4125-4aba-a3f6-5e0737581ad7_2' : base64.b64encode('STAGE-001'.encode("utf-8")).decode("utf-8"),
            'BitBytesData_ProcessingStages_Main-c88bb07a-4125-4aba-a3f6-5e0737581ad7_4' : base64.b64encode('Initialization'.encode("utf-8")).decode("utf-8"),
            'BitBytesData_ProcessingStages_Main-c88bb07a-4125-4aba-a3f6-5e0737581ad7_6' : base64.b64encode('Process BitBytes application request'.encode("utf-8")).decode("utf-8"),
            'BitBytesData_ProcessingStages_Main-c88bb07a-4125-4aba-a3f6-5e0737581ad7_8' : base64.b64encode('Pending'.encode("utf-8")).decode("utf-8")}
                        que2 = Queue.Queue()
                        t2 = Thread(target=lambda q, arg1,arg2,arg3: q.put(sendBridge(arg1,arg2,arg3)), args=(que2,bridgeData,'BitBytesData_ProcessingStages',sendData2))
                        t2.start()
                        t2.join()
                

                    elif flowName == "BitBytesData_DataProcessing" and MobileNumber != mNumber:
                        ##Operation1
                        sendData1 = {
            'BitBytesData_ApplicationModule_Main-dd6c6a33-8c39-46b8-9bae-c54d4bbe5ca5_2' : base64.b64encode('BitBytes'.encode("utf-8")).decode("utf-8"),
            'BitBytesData_ApplicationModule_Main-dd6c6a33-8c39-46b8-9bae-c54d4bbe5ca5_4' : base64.b64encode('1.0'.encode("utf-8")).decode("utf-8"),
            'BitBytesData_ApplicationModule_Main-dd6c6a33-8c39-46b8-9bae-c54d4bbe5ca5_6' : base64.b64encode('Processing'.encode("utf-8")).decode("utf-8"),
            'BitBytesData_ApplicationModule_Main-dd6c6a33-8c39-46b8-9bae-c54d4bbe5ca5_8' : base64.b64encode('DataProcessing'.encode("utf-8")).decode("utf-8")}
                        que1 = Queue.Queue()
                        t1 = Thread(target=lambda q, arg1,arg2,arg3: q.put(sendBridge(arg1,arg2,arg3)), args=(que1,bridgeData,'BitBytesData_ApplicationModule',sendData1))
                        t1.start()
                        t1.join()
                

                    elif flowName == "BitBytesData_ProcessingStages" and MobileNumber != mNumber:
                        ##Operation3
                        sendData3 = {
            'BitBytesData_CompletionTracking_Main-f2403890-e487-497b-81cb-25b8f563bf0d_2' : base64.b64encode('COMP-001'.encode("utf-8")).decode("utf-8"),
            'BitBytesData_CompletionTracking_Main-f2403890-e487-497b-81cb-25b8f563bf0d_4' : base64.b64encode('Pending'.encode("utf-8")).decode("utf-8"),
            'BitBytesData_CompletionTracking_Main-f2403890-e487-497b-81cb-25b8f563bf0d_6' : base64.b64encode('BitBytesAgent'.encode("utf-8")).decode("utf-8"),
            'BitBytesData_CompletionTracking_Main-f2403890-e487-497b-81cb-25b8f563bf0d_8' : base64.b64encode('Pending'.encode("utf-8")).decode("utf-8"),
            'BitBytesData_CompletionTracking_Main-f2403890-e487-497b-81cb-25b8f563bf0d_10' : base64.b64encode('Processing stage completed successfully'.encode("utf-8")).decode("utf-8")}
                        que3 = Queue.Queue()
                        t3 = Thread(target=lambda q, arg1,arg2,arg3: q.put(sendBridge(arg1,arg2,arg3)), args=(que3,bridgeData,'BitBytesData_CompletionTracking',sendData3))
                        t3.start()
                        t3.join()
                


                    #if flowName == "<FLOW NAME TO CHECK>":
                        #sendBridge(bridgeData,'<FLOW NAME TO REPLY>','<REPLY DATA>')
                        #sendWhisper(bridgeData,'<FLOW NAME TO REPLY>','<REPLY DATA>')
                        #sendBridgeToSet(bridgeData,'<FLOW NAME TO REPLY>','<REPLY DATA>','<SET NAME>)
                        #generateReport(bridgeData,'<FLOW NAME TO REPLY>')
                        #sendSpecific(bridgeData,'<FLOW NAME TO REPLY>')
                    #<YOUR CODE ENDS HERE>
                elif 'UpdatedTemplateJson' in data:
                    templateForAdmin = data['UpdatedTemplateJson']
                    forumIDCheck = templateForAdmin['ForumID']
                    if forumIDCheck == forumID:
                        admin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'BitBytesData_BitBytesData_Admin.txt')
                        with open(admin_path, 'w') as f:
                            json.dump(templateForAdmin, f)
    except Exception as e:
        print (e)

#------------------------------------------
#Send Bridge
#------------------------------------------

def sendBridge(bridgeData, replyFlow, replyData):
    try:
        TemplateID = bridgeData["TemplateID"]
        ForumID = bridgeData['ForumID']
        current_dir_path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir_path, 'BitBytesData_BitBytesData_Admin.txt'), 'r') as filePath:
            content = filePath.read()
        jsonData = json.loads(content)
        FID = jsonData['AdminFlow'][replyFlow]["FID"]
        tempJson ={
        "ForumID": ForumID,
        "SessionID": Sessionid,
        "MACAddress": MAC_ADDRESS,
        "Time": str(int(time.time() * 1000)),
        "ScheduledDateTime": "now",
        "ScheduledBoolean": 0,
        "FlowID": replyFlow,
        "EnableChat": 1,
        "FlowType": "Custom",
        "BridgeForward": 0,
        "TemplateID": TemplateID,
        "TextCount": 1,
        "ImageCount": 1,
        "InvoiceID": "",
        "DocumentCount": 0,
        "User": False,
        "VideoCount": 0,
        "ReplyBridgeID": "",
        "HiddenFlow": False,
        "TempBridgeId": str(uuid.uuid4()),
        replyFlow: replyData,
        "FID": FID,
        "ServerID": SERVER_ID,
        "SentTo": '0'
        }
        variab = {"Data":json.dumps(tempJson)}
        up = {}
        response = requests.post(f'{API_BASE}/bridgeSendingToForum', files=up, data=variab, timeout=600)
        print (response)
        return response
    except Exception as e:
        print (e)
        return e


def sendUserRequestBridge(flow_name, message):
    try:
        global Sessionid
        if not Sessionid:
            login()

        admin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'BitBytesData_BitBytesData_Admin.txt')
        if not os.path.exists(admin_path):
            getForumDetails()
        with open(admin_path, 'r') as f:
            admin_data = json.load(f)

        template_id = admin_data.get('TemplateID', '4c707a3b-a18a-4ca2-96fb-64c9aaf25d95')

        if flow_name == 'BitBytesData_ApplicationModule':
            payload = {
                'BitBytesData_ApplicationModule_Main-dd6c6a33-8c39-46b8-9bae-c54d4bbe5ca5_2': base64.b64encode('BitBytes'.encode('utf-8')).decode('utf-8'),
                'BitBytesData_ApplicationModule_Main-dd6c6a33-8c39-46b8-9bae-c54d4bbe5ca5_4': base64.b64encode('1.0'.encode('utf-8')).decode('utf-8'),
                'BitBytesData_ApplicationModule_Main-dd6c6a33-8c39-46b8-9bae-c54d4bbe5ca5_6': base64.b64encode('Processing'.encode('utf-8')).decode('utf-8'),
                'BitBytesData_ApplicationModule_Main-dd6c6a33-8c39-46b8-9bae-c54d4bbe5ca5_8': base64.b64encode(message.encode('utf-8')).decode('utf-8')
            }
        elif flow_name == 'BitBytesData_ProcessingStages':
            payload = {
                'BitBytesData_ProcessingStages_Main-c88bb07a-4125-4aba-a3f6-5e0737581ad7_2': base64.b64encode('STAGE-001'.encode('utf-8')).decode('utf-8'),
                'BitBytesData_ProcessingStages_Main-c88bb07a-4125-4aba-a3f6-5e0737581ad7_4': base64.b64encode('Active'.encode('utf-8')).decode('utf-8'),
                'BitBytesData_ProcessingStages_Main-c88bb07a-4125-4aba-a3f6-5e0737581ad7_6': base64.b64encode(message.encode('utf-8')).decode('utf-8'),
                'BitBytesData_ProcessingStages_Main-c88bb07a-4125-4aba-a3f6-5e0737581ad7_8': base64.b64encode('In Progress'.encode('utf-8')).decode('utf-8')
            }
        elif flow_name == 'BitBytesData_CompletionTracking':
            payload = {
                'BitBytesData_CompletionTracking_Main-f2403890-e487-497b-81cb-25b8f563bf0d_2': base64.b64encode('COMP-001'.encode('utf-8')).decode('utf-8'),
                'BitBytesData_CompletionTracking_Main-f2403890-e487-497b-81cb-25b8f563bf0d_4': base64.b64encode(datetime.now().strftime('%H:%M:%S').encode('utf-8')).decode('utf-8'),
                'BitBytesData_CompletionTracking_Main-f2403890-e487-497b-81cb-25b8f563bf0d_6': base64.b64encode('BitBytesAgent'.encode('utf-8')).decode('utf-8'),
                'BitBytesData_CompletionTracking_Main-f2403890-e487-497b-81cb-25b8f563bf0d_8': base64.b64encode('Success'.encode('utf-8')).decode('utf-8'),
                'BitBytesData_CompletionTracking_Main-f2403890-e487-497b-81cb-25b8f563bf0d_10': base64.b64encode(message.encode('utf-8')).decode('utf-8')
            }
        else:
            flow_name = 'BitBytesData_DataProcessing'
            payload = {
                'BitBytesData_DataProcessing_Main-17c6bca0-5246-4ff1-a384-f9262bef2d0b_2': base64.b64encode('PROC-001'.encode('utf-8')).decode('utf-8'),
                'BitBytesData_DataProcessing_Main-17c6bca0-5246-4ff1-a384-f9262bef2d0b_4': base64.b64encode('JSON'.encode('utf-8')).decode('utf-8'),
                'BitBytesData_DataProcessing_Main-17c6bca0-5246-4ff1-a384-f9262bef2d0b_8': base64.b64encode(message.encode('utf-8')).decode('utf-8')
            }

        fid = admin_data['AdminFlow'][flow_name]['FID']

        tempJson = {
            'ForumID': forumID,
            'SessionID': Sessionid,
            'MACAddress': MAC_ADDRESS,
            'Time': str(int(time.time() * 1000)),
            'ScheduledDateTime': 'now',
            'ScheduledBoolean': 0,
            'FlowID': flow_name,
            'EnableChat': 1,
            'FlowType': 'Custom',
            'BridgeForward': 0,
            'TemplateID': template_id,
            'TextCount': 1,
            'ImageCount': 1,
            'InvoiceID': '',
            'DocumentCount': 0,
            'User': False,
            'VideoCount': 0,
            'ReplyBridgeID': '',
            'HiddenFlow': False,
            'TempBridgeId': str(uuid.uuid4()),
            flow_name: payload,
            'FID': fid,
            'ServerID': SERVER_ID,
            'SentTo': '0'
        }

        res = requests.post(f'{API_BASE}/bridgeSendingToForum', data={'Data': json.dumps(tempJson)}, files={}, timeout=30)
        resp_data = res.json()
        bridge_id = resp_data.get('ErrorMessage')
        return {
            'success': True,
            'bridgeId': bridge_id,
            'flow': flow_name,
            'raw': resp_data
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


if __name__ == "__main__":
    go()


#End of bot code