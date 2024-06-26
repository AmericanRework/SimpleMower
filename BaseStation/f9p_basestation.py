"""
f9p_basestation.py

Survey your base station antenna location to best possible accuracy - I used rtk2go.com and https://github.com/semuconsulting/PyGPSClient
Fill in the lat/lon/height below. 
run this python script, then run the command line down at the bottom of this comment. 

install: (I might have missed something here:)
python3 -m pip install --upgrade pygnssutils
pip3 install typing-extensions


Example showing how to configure a u-blox ZED-F9P
receiver to operate in RTK Base Station mode (either
Survey-In or Fixed Timing Mode). This can be used to
complement PyGPSClient's NTRIP Caster functionality.

It also optionally formats a user-defined preset
configuration message string suitable for copying
and pasting into the PyGPSClient ubxpresets file.

Created on 26 Apr 2022

:author: semuadmin
:copyright: SEMU Consulting © 2022
:license: BSD 3-Clause

command line ntrip server: This is working great! 
     I dont' think it has a uname or pw? I just used the anon-password combo in the example and it worked lol. 

gnssserver --inport "/dev/ttyACM0" --hostip 0.0.0.0 --outport 2101 --ntripmode 1 --protfilter 4 --format 2

"""

from serial import Serial

from pyubx2 import UBXMessage


import struct
from datetime import datetime, timedelta
from math import cos, pi, sin, trunc

from pynmeagps.nmeatypes_core import NMEA_HDR

import pyubx2.exceptions as ube
import pyubx2.ubxtypes_configdb as ubcdb
import pyubx2.ubxtypes_core as ubt
from pyubx2.ubxtypes_core import POLL, SET, UBX_HDR

TMODE_SVIN = 1
TMODE_FIXED = 2
SHOW_PRESET = True  # hide or show PyGPSClient preset string

def send_msg(serial_out: Serial, ubx: UBXMessage):
    """
    Send config message to receiver.
    """

    print("Sending configuration message to receiver...")
    print(ubx)
    serial_out.write(ubx.serialize())


def config_rtcm(port_type: str) -> UBXMessage:
    """
    Configure which RTCM3 messages to output.
    """

    print("\nFormatting RTCM MSGOUT CFG-VALSET message...")
    layers = 1  # 1 = RAM, 2 = BBR, 4 = Flash (can be OR'd)
    transaction = 0
    cfg_data = []
    for rtcm_type in (
        "1005",
        "1077",
        "1087",
        "1097",
        "1127",
        "1230",
    ):
        cfg = f"CFG_MSGOUT_RTCM_3X_TYPE{rtcm_type}_{port_type}"
        cfg_data.append([cfg, 1])

    ubx = UBXMessage.config_set(layers, transaction, cfg_data)

    if SHOW_PRESET:
        print(
            "Set ZED-F9P RTCM3 MSGOUT Basestation, "
            f"CFG, CFG_VALSET, {ubx.payload.hex()}, 1\n"
        )

    return ubx


def config_svin(port_type: str, acc_limit: int, svin_min_dur: int) -> UBXMessage:
    """
    Configure Survey-In mode with specied accuracy limit.
    """

    print("\nFormatting SVIN TMODE CFG-VALSET message...")
    tmode = TMODE_SVIN
    layers = 1
    transaction = 0
    acc_limit = int(round(acc_limit / 0.1, 0))
    cfg_data = [
        ("CFG_TMODE_MODE", tmode),
        ("CFG_TMODE_SVIN_ACC_LIMIT", acc_limit),
        ("CFG_TMODE_SVIN_MIN_DUR", svin_min_dur),
        (f"CFG_MSGOUT_UBX_NAV_SVIN_{port_type}", 1),
    ]

    ubx = UBXMessage.config_set(layers, transaction, cfg_data)

    if SHOW_PRESET:
        print(
            "Set ZED-F9P to Survey-In Timing Mode Basestation, "
            f"CFG, CFG_VALSET, {ubx.payload.hex()}, 1\n"
        )

    return ubx


def config_fixed(acc_limit: int, lat: float, lon: float, height: float) -> UBXMessage:
    """
    Configure Fixed mode with specified coordinates.
    """

    print("\nFormatting FIXED TMODE CFG-VALSET message...")
    tmode = TMODE_FIXED
    pos_type = 1  # LLH (as opposed to ECEF)
    layers = 1
    transaction = 0
    acc_limit = int(round(acc_limit / 0.1, 0))
    lats, lath = val2sphp(lat)
    lons, lonh = val2sphp(lon)

    height = int(height)
    cfg_data = [
        ("CFG_TMODE_MODE", tmode),
        ("CFG_TMODE_POS_TYPE", pos_type),
        ("CFG_TMODE_FIXED_POS_ACC", acc_limit),
        ("CFG_TMODE_HEIGHT_HP", 0),
        ("CFG_TMODE_HEIGHT", height),
        ("CFG_TMODE_LAT", lats),
        ("CFG_TMODE_LAT_HP", lath),
        ("CFG_TMODE_LON", lons),
        ("CFG_TMODE_LON_HP", lonh),
    ]

    ubx = UBXMessage.config_set(layers, transaction, cfg_data)

    if SHOW_PRESET:
        print(
            "Set ZED-F9P to Fixed Timing Mode Basestation, "
            f"CFG, CFG_VALSET, {ubx.payload.hex()}, 1\n"
        )

    return ubx
    
    
    
def val2sphp(val: float, scale: float = 1e-7) -> tuple:
    """
    Convert a float value into separate standard and high precisions components,
    multiplied by a scaling factor to render them as integers, as required by some
    CFG and NAV messages.

    e.g. 48.123456789 becomes (481234567, 89)

    :param float val: value as float
    :param float scale: scaling factor e.g. 1e-7
    :return: tuple of (standard precision, high precision)
    :rtype: tuple
    """

    val = val / scale
    val_sp = trunc(val)
    val_hp = round((val - val_sp) * 100)
    return val_sp, val_hp



if __name__ == "__main__":
    # Amend as required...
    PORT = "/dev/ttyACM0"
    PORT_TYPE = "USB"  # choose from "USB", "UART1", "UART2"
    BAUD = 115200
    TIMEOUT = 5


    TMODE = TMODE_FIXED  # "TMODE_SVIN" or 1 = Survey-In, "TMODE_FIXED" or 2 = Fixed
    ACC_LIMIT = 20  # accuracy in mm

    # only used if TMODE = SVIN ...
    SVIN_MIN_DUR = 90  # seconds

    # only used if TMODE = FIXED ...
    ARP_LAT = #YOUR LAT
    ARP_LON = #YOUR LON
    ARP_HEIGHT = #YOUR HEIGHT IN cm. yes I believe it's in centimeters.

    print(f"Configuring receiver on {PORT} @ {BAUD:,} baud.\n")
    with Serial(PORT, BAUD, timeout=TIMEOUT) as stream:

        # configure RTCM3 outputs
        msg = config_rtcm(PORT_TYPE)
        send_msg(stream, msg)

        # configure either Survey-In or Fixed Timing Mode
        if TMODE == TMODE_SVIN:
            msg = config_svin(PORT_TYPE, ACC_LIMIT, SVIN_MIN_DUR)
        else:
            msg = config_fixed(ACC_LIMIT, ARP_LAT, ARP_LON, ARP_HEIGHT)
        send_msg(stream, msg)
