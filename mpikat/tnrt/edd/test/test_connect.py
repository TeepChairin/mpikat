import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/user1/tnrtkat/mpikat/mpikat/tnrt/edd/')

import katcp_blocking_client as kat
mykat =kat.BlockingRequest("127.0.0.1", "6000")
mykat.start()     
#mykat.configure("test")
mykat.setup_sensors()
