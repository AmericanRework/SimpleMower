"""
pygnssutils - rtk_example.py

*** FOR ILLUSTRATION ONLY - NOT FOR PRODUCTION USE *** check out semuconsulting.com there was lots of text here. Follow their license.

modified to dump current position, accuracy and time of fix to /dev/shm/coords.txt
This is setup for an RTK base station at 10.10.0.9 or swap the commented lines and you can use rtk2go.com

install:
python3 -m pip install --upgrade pygnssutils
pip3 install typing-extensions
If it's not working, I have a vauge memory of running a factory reset on the f9 using the SEMU Consulting gnsutils gui app 'cause whatever I tried before this had it sending ood phrases? 
Must have gnssapp.py in same directory when you run this.


:original author: semuadmin (modified by AmericanRework)
:copyright: SEMU Consulting © 2022
:license: BSD 3-Clause
"""
# pylint: disable=invalid-name

from queue import Queue, Empty
from threading import Event
from time import sleep

from pygnssutils import VERBOSITY_LOW, GNSSNTRIPClient
from gnssapp import GNSSSkeletonApp

CONNECTED = 1

if __name__ == "__main__":
    # GNSS receiver serial port parameters - AMEND AS REQUIRED:
    SERIAL_PORT = "/dev/ttyACM0"
    BAUDRATE = 115200
    TIMEOUT = 10

    # NTRIP caster parameters - AMEND AS REQUIRED:
    # Ideally, mountpoint should be <30 km from location.
    IPPROT = "IPv4"  # or "IPv6"
#    NTRIP_SERVER = "rtk2go.com"
    NTRIP_SERVER = "10.10.0.9"
    NTRIP_PORT = 2101
#    NTRIP_PORT = 2101
    FLOWINFO = 0  # for IPv6
    SCOPEID = 0  # for IPv6
#    MOUNTPOINT = "closestMountPoint"  # leave blank to retrieve sourcetable
    MOUNTPOINT = "pygnssutils"  # leave blank to retrieve sourcetable
#    NTRIP_USER = "yourEmail"
#    NTRIP_PASSWORD = ""
    NTRIP_USER = "anon"
    NTRIP_PASSWORD = "password"

    # NMEA GGA sentence status - AMEND AS REQUIRED:
    GGAMODE = 0 # use fixed reference position (0 = use live position)
    GGAINT = -1  # interval in seconds (-1 = do not send NMEA GGA sentences)
    # Fixed reference coordinates (only used when GGAMODE = 1) - AMEND AS REQUIRED:
    
    REFLAT = 45.5887029 
    REFLON = -122.8135701
    REFALT = 299.9530
    REFSEP = 26.1743

    recv_queue = Queue()  # data from receiver placed on this queue
    send_queue = Queue()  # data to receiver placed on this queue
    stop_event = Event()
#    idonly = False #debug mode
    idonly = True #normal mode
#    tuple coords

    try:
        print(f"Starting GNSS reader/writer on {SERIAL_PORT} @ {BAUDRATE}...\n")
        with GNSSSkeletonApp(
            SERIAL_PORT,
            BAUDRATE,
            TIMEOUT,
            stopevent=stop_event,
            recvqueue=recv_queue,
            sendqueue=send_queue,
            idonly=idonly,
            enableubx=True,
            showhacc=True,
        ) as gna:
            gna.run()
            sleep(2)  # wait for receiver to output at least 1 navigation solution

            print(f"Starting NTRIP client on {NTRIP_SERVER}:{NTRIP_PORT}...\n")
            with GNSSNTRIPClient(gna, verbosity=VERBOSITY_LOW) as gnc:
                streaming = gnc.run(
                    ipprot=IPPROT,
                    server=NTRIP_SERVER,
                    port=NTRIP_PORT,
                    flowinfo=FLOWINFO,
                    scopeid=SCOPEID,
                    mountpoint=MOUNTPOINT,
                    ntripuser=NTRIP_USER,  # pygnssutils>=1.0.12
                    ntrippassword=NTRIP_PASSWORD,  # pygnssutils>=1.0.12
                    reflat=REFLAT,
                    reflon=REFLON,
                    refalt=REFALT,
                    refsep=REFSEP,
                    ggamode=GGAMODE,
                    ggainterval=GGAINT,
                    output=send_queue,  # send NTRIP data to receiver
                )

                while (
                    streaming and not stop_event.is_set()
                ):  # run until user presses CTRL-C
                    if recv_queue is not None:
                        # consume any received GNSS data from queue
                        try:
                            while not recv_queue.empty():
                                (raw, parsed) = recv_queue.get(False)
                                print(f"{'GNSS>> ' + parsed.identity if idonly else parsed}")
                                recv_queue.task_done()
                        except Empty:
                            pass
                    coords = gna.get_mycoordinates()
                    print(coords)
                    #OPEN A STATUS FILE FOR WRITING. 
                    (lat, lon, elv, sep, hac, time) = coords
                    coordFile = open("/dev/shm/coords.txt", "w")
                    #CLEAR SATUS FILE?
                    coordFile.write(f"{lat:.7f}\n{lon:.7f}\n{elv:.7f}\n{hac:.3f}\n{time:.1f}")
                    coordFile.close()
                    sleep(1)
                sleep(1)

    except KeyboardInterrupt:
        stop_event.set()
        print("Terminated by user")
