import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/user1/tnrtkat/mpikat/mpikat/tnrt/edd/')
import katcp_blocking_client as kat
import json

print "KATCP"

mykat = kat.BlockingRequest("127.0.0.1","5000")
print "connecting test ..."
mykat.start()
print "next"

# print "sensor list control"
# mykat.my_sensor_list_controlled()
# print "next"

# print "sensor control"
# mykat.my_sensor_control("dec")
# print "next"

# print "sensor_set"
# mykat.my_sensor_set("dec",0.2)
# print "next"

print "sensor control all"
mykat.my_sensor_list_controlled()
print "next"

# mykat.capture_start()
# mykat.capture_stop()
# mykat.deconfigure()
# mykat.stop()
print "Test pass"


