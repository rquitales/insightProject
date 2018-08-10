import time, sys, random, json, csv
from collections import defaultdict
from datetime import datetime
from kafka import KafkaProducer, KeyedProducer

sensorTopic = sys.argv[1]
ipFile = sys.argv[2]
seedFile = sys.argv[3]
positionInFile = int(sys.argv[4])
sensorType = sys.argv[5]
deviceTotal = int(sys.argv[6])
if len(sys.argv) > 7:
    deviceIDStart = int(sys.argv[7])
else:
    deviceIDStart = 1

#Function to format new seed data entries into defaultdict structure.
def insertEntry(dictionary, deviceID, latitude, longitude, value):
    dictionary[str(deviceID)] = {'latitude': latitude, 'longitude' : longitude, 'value' : value, 'ctime' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

#Function to read unique number of lines in seed data file.
def createSeedData(filename, numOfDevices = 100, start = 1):
    seedData = {}
    with open(filename, 'r') as csvfile:
        rowPosition = 0
        d_id = deviceIDStart
        for row in csv.DictReader(csvfile):
            rowPosition += 1
            if rowPosition < start:
                continue
            insertEntry(seedData, d_id, row['Latitude'], row['Longitude'], float(row['Values']))
            d_id += 1
            if (rowPosition - start) + 2 > numOfDevices:
                break
    return seedData

#Modify seed data's sensor value for randomisations/simulations.
def modifyReading(dictionary):
    for device in dictionary:
        dictionary[device]['value'] = dictionary[device]['value'] + random.randint(-5,5)
        dictionary[device]['ctime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#Send data to kafka.
def send2Kafka(ipAddresses, data, deviceKey):
    kProducer = (KafkaProducer(bootstrap_servers = ipAddresses, api_version=(0,10),
              value_serializer = lambda v: json.dumps(v).encode('utf-8')))
    kProducer.send(sensorTopic, {sensorType: {'deviceID' : deviceKey, 'latitude' : data[deviceKey]['latitude'], 'longitude' : data[deviceKey]['longitude'], 'value' : data[deviceKey]['value'], 'ctime' : data[deviceKey]['ctime']}})
    kProducer.flush()

def main():
    #Create seed data.
    seedData = createSeedData(seedFile, numOfDevices = deviceTotal, start = positionInFile)
    #Get Kafka IP addressesself.
    ipAddresses = open(ipFile, 'r')
    ip = ipAddresses.read()
    ipAddresses.close()
    ip = ip.split(",")
    for devKey in seedData.keys():
        send2Kafka(ip, seedData, devKey)
    i = 0
    while i < 10000000000000:
        modifyReading(seedData)
        for devKey in seedData.keys():
            send2Kafka(ip, seedData, devKey)
        i += 1
        time.sleep(1)

if __name__ == "__main__":
  main()