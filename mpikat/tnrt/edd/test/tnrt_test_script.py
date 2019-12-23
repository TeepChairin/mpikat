import katcp_blocking_client as kat
import json

print "KATCP"

mykat = kat.BlockingRequest("127.0.0.1","6000")
config1 =   {
                "packetisers":
                [
                    {
                        "id": "ubb_digitiser",
                        "address": ["127.0.0.1", 7147],
                        "sampling_rate": 2600000000.0,
                        "bit_width": 12,
                        "v_destinations": "225.0.0.152+3:7148",
                        "h_destinations": "225.0.0.156+3:7148",
                        "interface_addresses": {
                            "0":"10.10.1.30",
                            "1":"10.10.1.31"
                        }
                    }
                ],
                "products":
                [
                    {
                        "id": "dspsr_pipeline",
                        "type": "server",
                        "pipeline": "DspsrPipelineSrxdev",
                        "mc_source":"239.2.1.150",
                        "central_freq":"1400"
                    }
                ],
                "fits_interfaces":
                [
                    {
                        "id": "fits_interface_01",
                        "name": "FitsInterface",
                        "address": ["134.104.70.63", 5000],
                        "nbeams": 2,
                        "nchans": 2048,
                        "integration_time": 256,
                        "blank_phases": 1
                    }
                ]
            }
config2 =   {
                "packetisers":
                [
                    {
                        "id": "ubb_digitiser",
                        "address": ["172.17.0.5", 7147],
                        "sampling_rate": 2600000000.0,
                        "bit_width": 12,
                        "v_destinations": "225.0.0.152+3:7148",
                        "h_destinations": "225.0.0.156+3:7148",
                        "interface_addresses": {
                            "0":"10.10.1.30",
                            "1":"10.10.1.31"
                        }
                    }
                ],
                "products":
                [
                    {
                        "id": "dspsr_pipeline",
                        "type": "server",
                        "pipeline": "DspsrPipelineSrxdev",
                        "mc_sources":"239.2.1.150",
                        "central_freq":"1400",
                        "servers":
                        [
                            {
                                "sources": "spead://239.2.1.150:7147",
                            },
                            {
                                "sources": "spead://239.2.1.150:7147",
                            }
                        ]
                    }
                ],
                "fits_interfaces":
                [
                    {
                        "id": "fits_interface_01",
                        "name": "FitsInterface",
                        "address": ["134.104.70.63", 5000],
                        "nbeams": 2,
                        "nchans": 2048,
                        "integration_time": 256,
                        "blank_phases": 1
                    }
                ]
            }
config3 =   {
                "mode": "Search1Beam",
                "nbands": 48,
                "frequency": 1340.5,
                "nbeams": 18,
                "band_offset": 0,
                "write_filterbank": 0
            }
config4 = {
    "packetisers":
    [
    ],
    "products":
    [
    ],
    "fits_interfaces":
    [
    ]
}
print "connecting test ..."
mykat.start()
print "connecting complete"
backend_config_json = json.dumps(config2)  # Convert sting to json format
print "configure testing ..."
mykat.configure(backend_config_json)
print "configure testing complete"
print "dspsr start"
mykat.my_dspsr_test()

# mykat.capture_start()
# mykat.capture_stop()
# mykat.deconfigure()
# mykat.stop()

print "Test pass"


