"""
TobyAuto1.2.py - remote control and very basic rtk GPS of a rover. Use this code at your own risk!!! 
If youre smart enough to make this work, you're smart enough not to misuse it.


start rtk_example.py, myTobyServer.js, and then this(TobyAuto1.2.py.)
remote only, no gps: just start myTobyServer then this.

Install:
sudo pip3 install Adafruit_BBIO
pyserial
probably other stuff. use google.
must get the myTobyServer.js (or some other code) writing to dev/shm/keyCommands.txt before this will do anything.

"""


import serial
import time
from datetime import datetime
import math
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC
import rcpy 
import rcpy.mpu9250 as mpu9250


#onboard serial ports: yes tty00 is a port. what now the tty01 no longer works and must use ttyS1?! wtf. I did plug in a 2nd cable to the gps serial port?
ser1 = serial.Serial(port = "/dev/ttyS1", baudrate=115200, timeout = 0.1)
ser2 = serial.Serial(port = "/dev/ttyS2", baudrate=115200, timeout = 0.1)

#alternatively use a usb serial port: works.
#ser = serial.Serial(port = "/dev/ttyACM2", baudrate=115200)


faulted = False
faultMessageLogged = False
estop = False
bumpers = False
directionCommand = 'o'
cutCommand = 'o'
previousCommand = 'o'
loopCount = 0
okToRun = True
speedCommand = 1
rMtrCurrent = 0
lMtrCurrent = 0
mMtrCurrent = 0
lat = 0
lon = 0
hac = 0
prevLat = 0
prevLon = 0
prevHac = 0  #yes we need this.
gpsHeading = 0 #0-360, from last two gps points
timeCurrentFix = 0
prevFixTime = 0
gpsVelocity = 0 #m/s? or ? let's try for m/s. .00001 angle is ~1.1m so multiply by 110000
imuHeading = 0 #let's see what it can do? might want imu rate of turn to see if we're turning?
imuHorizTurnRate = 0 #deg/sec?
desiredHeading = 0 #0-360
moveType = 0
imuTemp = 0
avgMagHeading = 0 #0-360
bonkEast = False
bonkWest = False
bonkSouth = False
bonkNorth = False
bonkCorner = False
headingMet = True
batteryVoltage = 0
zoneSet = 0
faultMessage = "uninit"

def main():
    rcpy.set_state(rcpy.RUNNING)
    mpu9250.initialize(enable_magnetometer = True)
    
    #lol @ global vars. All so we can have functions that we can pass stuff around.
    global faulted, estop, bumpers, directionCommand ,cutCommand ,previousCommand ,loopCount, okToRun ,speedCommand, rMtrCurrent , lMtrCurrent ,mMtrCurrent
    global lat, lon ,hac ,prevLat ,prevLon ,prevHac , gpsHeading , timeCurrentFix , prevFixTime , gpsVelocity , imuHeading ,imuHorizTurnRate
    global desiredHeading , moveType ,imuTemp ,avgMagHeading , bonkEast , bonkWest , bonkSouth , bonkNorth , bonkCorner , headingMet ,zoneSet , batteryVoltage
    global ser1, ser2, faultMessageLogged, faultMessage
    
    
    
    ADC.setup()
    
    
    #to install: sudo pip3 install Adafruit_BBIO
    #for pin-to-plug #'s' check out https://github.com/adafruit/adafruit-beaglebone-io-python/blob/master/source/common.c
    # head over to  /sys/class/gpio/ for each individual pin. echo 1 > active_low (or 0 for active high)
    # doing a setup: echo 1 > active low for pins 49 and 113
    #may need?: you can use sudo usermod -a -G gpio userName to add userName to the group.
    #test setup - 2k resistor to either high or low. all work but pull ups aren't good yet.
    # check out 
    button="P8_9"  # PAUSE=P8_9, MODE=P8_10
    bumper1 = "GP0_3" # aka 1_25? always pulled up?! wtf?! 57 purpose: fwd/bkwd bump. 0 when not bumped. 2k inline reistor to a hall that pulls down.
    bumper2 = "GP0_5" #aka 3_20 pulled up. 116 Purpose: fwd/bkwd bump. 0 when not bumped.
    bumper3 = "GP1_3" #aka 3_1? pulled up 98 Purpose: lifted. 0 if not lifted - currently disconnected 'cause tiny bbblue connectors suck
    bumper4 = "GP1_4" #aka pulled up 97 Purpose: lifted. 0 if not lifted.
    estopBtn = "GP0_6" #aka 3_17 and P9_28 pulled down internally. fix 113 
    #fix below only swaps logic - still have to pull it up to 3.3v with 2k resistor to get a logic change.
    # estopBtn contd: 0 when not pressed.
    spare1 =  "P9_23" # aka 1_17 and P9_23 pulled down before fix 49 
    #see fix 113 estop btn for wiring info.
    LED   ="USR3"
    
    # Set the GPIO pins:
    GPIO.setup(LED,    GPIO.OUT)
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(bumper1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(bumper2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(bumper3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(bumper4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(estopBtn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(spare1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    #pull up-down doesn't work. boo. set manually?
    ioFile = open("/sys/class/gpio/gpio49/active_low", "w")
    ioFile.write("1")
    ioFile.close()
    
    ioFile = open("/sys/class/gpio/gpio113/active_low", "w")
    ioFile.write("1")
    ioFile.close()
    
    #open web interface file.
    commands = open("/dev/shm/KeyCommands.txt", "w")
    commands.write('o')
    commands.close()
    

    clearFaultFile()
    
    while(True):
        #sensor section ######################################################
        print(GPIO.input(bumper1))
        print(GPIO.input(bumper2))
        #print(GPIO.input(bumper3)) #these are lifted sensors that we accidentally ripped the connector off the bbblue board *sigh*
        #print(GPIO.input(bumper4))
        print(GPIO.input(estopBtn))
        #print(GPIO.input(spare1))
        
		#edit this to get your battery voltage correct for whatever voltage divider you use. suggest calibrating at various temperatures.
        batteryVoltage = 66.6 * ADC.read("AIN1") -30.35 #.70 at 16.5 v, .76 at 20.5. ... wtf this floats around +/- 0.25v? split difference?
        #errors continue - yesterday temp was almost freezing in the morning - 35 or 36 on the imu - and batt voltage faulted out. made revision to the gps battery threshold to depend on temp, we'll see! Needs a high temp shutoff or it runs batttery below 18v but still reads voltage as 19v *sigh*
        print(batteryVoltage)

        #OPEN A STATUS FILE FOR WRITING. 
        statusFile = open("/dev/shm/RobotStatus.txt", "w")
        #CLEAR SATUS FILE?
        statusFile.write(f"Battery: {batteryVoltage:.2f}")
        if ser1.isOpen() and ser2.isOpen():
            statusFile.write("servo amp: connected\n\n")
            faulted = False
        else:
            statusFile.write("servo amp: Failed coms\n")
            faulted = True
            dumpFaultState("Failed coms on at least one servo amp\n")
        
        #Check MTR currents
        ser1.reset_input_buffer() #was crashing if we had an OVC - this is the first read of the serial buffer and you can't make a float out of an ovc error message 
        ser2.reset_input_buffer() #dump input buffers just in case.
        ser1.write(str.encode('C\n'))
        ser2.write(str.encode('C\n'))
        lMtrCurrent = float(ser1.readline())
        rMtrCurrent = float(ser1.readline())
        mMtrCurrent = float(ser2.readline())
        ser2.readline() #not sure if we have to clear ser2 buffer but let's do that.
        reply = f"left: {lMtrCurrent:.2f} right: {rMtrCurrent:.2f} mow: {mMtrCurrent:.2f} "
        statusFile.write(reply + "\n")
        print(reply)
        if lMtrCurrent > 500 or rMtrCurrent > 500 or mMtrCurrent > 500:
            faulted = True
            print("Overcurrent! nooo!") #one time it failed when acm0 dissappeared, one time I forogot to start gps code.
            okToRun = False #pretty sure we want to force intervention in this case, but webpage maybe needs to reflect this error. 
            directionCommand = 'o'
            dumpFaultState("Overcurrent!")
        #400 is wheel spin on right motor, left was loaded up but only broke ... 70? we should probably look into this lol... the servo amps fault internally at '800' which is about 4-6 amps I think but I don't remember exactly the conversion.
        #cut motor is less than 5 when off, 15 to 40 when on.
        
        if (GPIO.input(bumper1) or GPIO.input(bumper2)): # broke the connector on board...  or GPIO.input(bumper3) or GPIO.input(bumper4)):
            statusFile.write("Bumpers: Bonk!!!\n")
            if loopCount < 10:
                statusFile.write("Bumpers: Override!\n")
                bumpers = False
                dumpFaultState("Bumper fault")
            else:
                bumpers = True
        else:
            statusFile.write("Bumpers: Clear \n")
            bumpers = False
        if GPIO.input(estopBtn):
            statusFile.write("Estop: Estopped\n")
            estop = True
            dumpFaultState("Estopped")
        else:
            statusFile.write("Estop: wheee \n")
            estop = False
        if (imuTemp > 42 and batteryVoltage < 18.5) or (imuTemp <= 42 and batteryVoltage < 18.0):
            estop = True
            faulted = True
            dumpFaultState("Battery Fault- 18v hard fault")
            #probably should try and shutdown at this point?
        
        #read more sensors here - Temp. onboard accelerometer/imu, gps. 
        saveLat = lat
        saveLon = lon
        saveHac = hac
        saveTime = timeCurrentFix
        try:
            gpsFile = open("/dev/shm/coords.txt", "r")
            lat = float(gpsFile.readline())
            lon = float(gpsFile.readline())
            gpsFile.readline() #elevation but not used for now?
            hac = float(gpsFile.readline())
            timeCurrentFix = float(gpsFile.readline())
            gpsFile.close()
        except:
            print("gps error")
        if saveTime == timeCurrentFix:
            gpsErrorCount = gpsErrorCount +1
            if gpsErrorCount > 10:
                faulted = True
                print("gps not changing - Error") #one time it failed when acm0 dissappeared, one time I forogot to start gps code.
                okToRun = False #pretty sure we want to force intervention in this case, but webpage maybe needs to reflect this error. 
                directionCommand = 'o'
                dumpFaultState("gps not changing - Error")
        else:
            gpsErrorCount = 0
        if ((saveLat == lat) and (saveLon == lon)): #stuck
            #stuck-timer or update timer?
            stuckTimer = stuckTimer + 1 #might be we're on the edge of a coord-line or just wobbling but still stuck. needs a stuck-coord project
            if stuckTimer > 10:
                faulted = True
                print("gps not changing - stuck") #one time it failed when acm0 dissappeared, one time I forogot to start gps code.
                okToRun = False #pretty sure we want to force intervention in this case, but webpage maybe needs to reflect this error. 
                directionCommand = 'o'
                dumpFaultState("gps not changing - stuck")
        else:
            stuckTimer = 0
            prevLat = saveLat
            prevLon = saveLon
            prevHac = saveHac
            prevFixTime = saveTime
            #calculate heading and velocity. ONLY if we have new gps coords!
            deltaLat = lat - prevLat
            deltaLon = lon - prevLon + 0.0000000001 #(+.0...01 to avoid divide by zero)
            deltaTime = (timeCurrentFix - prevFixTime)/1000 + 0.0000000001 #time is in msec, convert to seconds, & make sure we never divide by zero.
            if(deltaLon > 0):
                gpsHeading = 90 - math.degrees(math.atan(deltaLat/deltaLon))
            else:
                gpsHeading = 270 - math.degrees(math.atan(deltaLat/deltaLon))
            gpsVelocity = math.sqrt(deltaLat**2 + deltaLon**2) *110000/ deltaTime
            print(f"gps heading: {gpsHeading:.1f} velocity: {gpsVelocity:.7f}")
            print(f"{lat:.7f} {lon:.7f} {hac:.3f} {timeCurrentFix:.1f}")
        

        
        #Magnetometer. heh. There's a spreadsheet that helped get this set up.
        if rcpy.get_state() == rcpy.RUNNING:
            try:
                imuTemp = mpu9250.read_imu_temp()
                imuData = mpu9250.read()
            except:
                print("magnetometer error")
                dumpFaultState("magnetometer error")
            rawMagX = imuData['mag'][0]
            rawMagZ = imuData['mag'][2]
            if rawMagX < 5: rawMagX = 5
            if rawMagX > 45: rawMagX = 45
            if rawMagZ < -4: rawMagZ = -4
            if rawMagZ > 40: rawMagZ = 40
            HeadingXmag = math.degrees(math.asin((rawMagX-25)/20))+20
            HeadingZmag = math.degrees(math.acos((rawMagZ-18)/22))+20
         #   print(f"rawX: {rawMagX:.1f} rawZ: {rawMagZ:.1f}")
         #   print(f"pre-corrections magX: {HeadingXmag:.1f} P.C. magZ: {HeadingZmag:.1f}")
            if (HeadingXmag > 135 or HeadingZmag > 135 or HeadingXmag < 0):
                if rawMagX < 28:
                    HeadingZmag = 405 - HeadingZmag
                if rawMagZ < 24:
                    HeadingXmag = 225 - HeadingXmag
                HeadingXmag = (360+ HeadingXmag)%360
                HeadingZmag = (360+ HeadingZmag)%360
                if HeadingXmag < 90:
                    avgMagHeading = HeadingXmag + 360
                else:
                    avgMagHeading = HeadingXmag
                if HeadingZmag < 90:
                    avgMagHeading = avgMagHeading + HeadingZmag + 360
                else:
                    avgMagHeading = avgMagHeading + HeadingZmag
                avgMagHeading = (avgMagHeading /2)%360
            else:
                avgMagHeading = HeadingXmag
            
            magHeading = avgMagHeading
            #sigh. can't average 350 and 4....   was avgMagHeading = (HeadingXmag + HeadingZmag)/2
         #   print(f"magX: {HeadingXmag:.1f} magZ: {HeadingZmag:.1f}")
            print(f"magnetometer heading: {avgMagHeading:.1f} and Temp = {imuTemp:.1f}")
            #seems like we're a little ... oval shaped? in our compass. but close enough. it's mostly continuous, mostly matches gps too I think.
            #it would be awesome to make a self cal routine that uses gps heading driving itself on various angles? IDK if that would even be good enough.
        
        statusFile.write(f"gps coords: {lat:.7f}, {lon:.7f}, hac: {hac:.1f},  gps heading: {gpsHeading:.1f}, velocity: {gpsVelocity:.7f}, magHeading: {avgMagHeading:.1f}, Temp = {imuTemp:.1f}\n")
        
        #start of driving section: #################################################
        
        reply = "serial needs work - no response"
        #move motors based on KeyCommands input file:
        #read keyCommands.txt, switch/case/if block for turn left/right/toggle cut motor, etc...
        commands = open("/dev/shm/KeyCommands.txt", "r")
        inputCommand = commands.readline()
        statusFile.write(faultMessage)
        statusFile.write(" Previous command: \n")
        statusFile.write(inputCommand)
        statusFile.close()
        
        #reset faults on new key press:
        #grace time for new commands if bumpers are pressed:
        if inputCommand != previousCommand:
            previousCommand = inputCommand
            loopCount = 0
            stuckTimer = 0
            gpsErrorCount = 0
            okToRun = True
            faultMessageLogged = False
            faultMessage = ""
            if inputCommand == '1' or inputCommand == '2' or inputCommand == '3' or inputCommand == '4':
                zoneSet = 0
        if not faulted and not bumpers and not estop and okToRun:
            print("All systems go")
            #GPS-auto mode!!!
            if inputCommand == 'g' or directionCommand == 'g':
                directionCommand = 'g'
                print("running auto mode with GPS")
                #could use speedCommand to also choose zone 'cause we want a pretty consistent mowing speed
                if zoneSet == 0 and (speedCommand == 1 or speedCommand == 2 or speedCommand == 3 or speedCommand == 4):
                    setZone(speedCommand)
                speedCommand = 4 #this seems like good compromise of battery, cut speed/quality, and control. will slow @ boundary in v2.0.
                
                if (imuTemp > 42 and batteryVoltage < 19.0) or (imuTemp <= 42 and batteryVoltage < 18.5):
                    #ideally start to go home but for now just fault. #at super cold temps this is even more wrong. 35.7 imu temp he's faulting out at 18.4 even though he's fully charged.
                    #this might still not be high enough threshold, would like to correct this in a future version.
                    faulted = True
                    okToRun = False   
                    directionCommand = 'o'
                    print("Battery low!")
                    dumpFaultState("battery low - GPS")
                if hac > 100:
                    #gps accuracy is bad - worse than 10cm
                    faulted = True
                    okToRun = False   
                    directionCommand = 'o'
                    dumpFaultState("GPS accuracy above 10cm, stopping gps")
                #Temp is kinda funky. seems like maybe off 20 deg or so? 72f outside reports imuTemp 60 but robot is in sun so might be more like robot is 80?
                #no idea if 70 is about right or we should go more. starting low it should be about 80f.
                if imuTemp > 70: #need a couple temp levels - the big one is no charging below ... 32f I think? and no discharge above say 110f and no charge above 90f?
                    faulted = True
                    okToRun = False   
                    directionCommand = 'o'
                    dumpFaultState("Over Temperature!")
             
                #are we at ~shutdown past edge? shutdown (no resart until new command or just start up if someone kicks us back into bounds?)
                #N S E W
                if(lat >  north or lat < south or lon > east or lon < west):
                    faulted = True
                    okToRun = False #do we really want this to require intervention to fix or just drag it inbounds and away we go!?   
                    directionCommand = 'o'
                    print("out of boundary")
                    dumpFaultState('out of boundary')
                #additional flat area: delete the east check above, and add this:
                #if (lon > xx.xxxxxxxx  and lat less than south side of garden and lon greater than east side of flat, good to mow.
                #but not yet.
                
                #fence gps corners are absolute shutdown not 'start trying to turn'
                #Check corners before edges.
                #moveType: 0 = no move, 5= straight, 6 = reverse.
                #movetype contd: 1 = sharp turn left, 2 = sharp turn right, 3 = gradual turn left, 4 = gradual turn right. 
                #NE
                elif lat >  (north - 2*shutdownWidth) and lon > (east - 2*shutdownWidth):
                    print("in NE corner")
                    desiredHeading = 225
                    if not bonkCorner or (gpsVelocity > .2 and (gpsHeading < 180 or gpsHeading > 270)) :
                        headingMet = False
                        bonkCorner = True
                        if angleCompare(45,magHeading,180):
                            moveType = 2
                        else:
                            moveType = 1
                #NW
                elif lat >  (north - 2*shutdownWidth) and lon < (west + 2*shutdownWidth):
                    print("in NW corner")
                    desiredHeading = 135
                    if not bonkCorner or (gpsVelocity > .2 and (gpsHeading < 90 or gpsHeading > 180)) :
                        headingMet = False
                        bonkCorner = True
                        if angleCompare(315,magHeading,180):
                            moveType = 2
                        else:
                            moveType = 1
                #SE
                elif lat < (south + 2*shutdownWidth) and  lon > (east - 2*shutdownWidth):
                    print("in SE corner")
                    desiredHeading = 315
                    if not bonkCorner or (gpsVelocity > .2 and (gpsHeading > 0 and gpsHeading < 270 )) :
                        headingMet = False
                        bonkCorner = True
                        if angleCompare(135,magHeading,180): #was magHeading > 135:
                            moveType = 2
                        else:
                            moveType = 1
                #SW
                elif lat < (south + 2*shutdownWidth) and lon < (west + 2*shutdownWidth):
                    print("in SW corner")
                    desiredHeading = 45
                    if not bonkCorner or (gpsVelocity > .2 and (gpsHeading > 90 and gpsHeading < 360)) : #re-check using either gps or mag or both. 
                        bonkCorner = True
                        headingMet = False
                        if angleCompare(225,magHeading,180): # was magHeading > 225 , ang compare is 1 if a1 < a2
                            moveType = 2
                        else:
                            moveType = 1
                else:
                    bonkCorner = False
               
                #Check edges! Need to add edge-re-turn if mag heading and at the edge.
                if not bonkCorner:
                    #North
                    if lat >  (north - shutdownWidth):
                        print("bonked north")
                        if (not bonkNorth) or (gpsVelocity > .2 and (gpsHeading < 120 or gpsHeading > 240)) : # run this stuff when we first bonk or gps says wrong way
                            bonkNorth = True
                            if gpsHeading > 60 and gpsHeading < 100:
                                desiredHeading = 120
                                moveType = 4
                                headingMet = False
                            elif gpsHeading > 260 and gpsHeading < 300:
                                desiredHeading = 240
                                moveType = 3
                                headingMet = False
                            elif gpsHeading < 180:
                                desiredHeading = 180
                                moveType = 2
                                headingMet = False
                            else:
                                desiredHeading = 180
                                moveType = 1
                                headingMet = False
                    else:
                        bonkNorth = False
                    #South
                    if lat < (south + shutdownWidth):
                        print("bonked south")
                        if (not bonkSouth) or (gpsVelocity > .2 and (gpsHeading > 60 and gpsHeading < 300)):
                            bonkSouth = True
                            if gpsHeading > 80 and gpsHeading < 120:
                                desiredHeading = 60
                                moveType = 3
                                headingMet = False
                            elif gpsHeading > 240 and gpsHeading < 280:
                                desiredHeading = 300
                                moveType = 4
                                headingMet = False
                            elif gpsHeading < 180:
                                desiredHeading = 1 #does 0 not work?
                                moveType = 1
                                headingMet = False
                            else:
                                desiredHeading = 1
                                moveType = 2
                                headingMet = False
                    else:
                        bonkSouth = False
                    #East
                    if lon > (east - shutdownWidth):
                        print("bonked east")
                        if (not bonkEast) or (gpsVelocity > .2 and (gpsHeading < 210 or gpsHeading > 330)):
                            bonkEast = True
                            if gpsHeading > 150 and gpsHeading < 190:
                                desiredHeading = 330
                                moveType = 4
                                headingMet = False
                            elif (gpsHeading > 0 and gpsHeading < 30) or (gpsHeading > 350 and gpsHeading < 360):
                                desiredHeading = 210
                                moveType = 3
                                headingMet = False
                            elif gpsHeading < 90:
                                desiredHeading = 300 # 270 is kina sw for our setup trying 290
                                moveType = 1
                                headingMet = False
                            else:
                                desiredHeading = 300
                                moveType = 2
                                headingMet = False
                    else:
                        bonkEast = False        
                    #West
                    if lon < (west + shutdownWidth):
                        print("bonked West")
                        if (not bonkWest) or (gpsVelocity > .2 and (gpsHeading < 30 or gpsHeading > 150)):
                            bonkWest = True
                            if (gpsHeading > 0 and gpsHeading < 10) or (gpsHeading > 330 and gpsHeading < 360):
                                desiredHeading = 30
                                moveType = 4
                                headingMet = False
                            elif gpsHeading > 170 and gpsHeading < 210:
                                desiredHeading = 150
                                moveType = 3
                                headingMet = False
                            elif gpsHeading < 270:
                                desiredHeading = 90
                                moveType = 1
                                headingMet = False
                            else:
                                desiredHeading = 90
                                moveType = 2
                                headingMet = False
                    else:
                        bonkWest = False

                #not in any boundaries! Go straight.
                if not bonkWest and not bonkEast and not bonkNorth and not bonkSouth and not bonkCorner:
                    print("in bounds")
                    moveType = 5
                    cutCommand = 'M'
                  
                #check if heading met. on sharp turns we're always going to over-turn by 90deg or so. 
                print(f"moveType before heading met {moveType}")
                #sharp turn left
                if not headingMet:
                    if moveType == 1 and angleCompare(magHeading-45,desiredHeading,120):
                        headingMet = True
                        moveType = 5
                    if moveType == 3 and angleCompare(gpsHeading,desiredHeading,120):
                        headingMet = True
                        moveType = 5
                    if moveType == 2 and angleCompare(desiredHeading, magHeading+45,120):
                        headingMet = True
                        moveType = 5
                    if moveType == 4 and angleCompare(desiredHeading, gpsHeading,120):
                        headingMet = True
                        moveType = 5
                
                print(f"moveType is {moveType}")
                # run motors accordingly
                if moveType == 1:
                    sharpTurnLeft(ser1)
                if moveType == 2:
                    sharpTurnRight(ser1)
                if moveType == 3:
                    manualTurn(ser1, 2,8)
                if moveType == 4:
                    manualTurn(ser1, 8,2)
                if moveType == 5:
                    manualTurn(ser1, 4*speedCommand, 4.4*speedCommand) #straight isn't straight. heh. 4 and 5 it turns right. 4 and 4 is left.
                if moveType == 6:
                    reverse(ser1)
                    
        #add: move home when press h (or bat volt low)
            #compute target vector & speed
                #kinda like movesafe, but testing getting to points, following path between points.
            #is target vector more than 20 deg off from current direction? if yes do abrupt turn
            #otherwise do gradual turn. Go straight if within (5?) deg of desired direction. 
                
            #forward slow
            if inputCommand == 'w' or directionCommand == 'w':
                directionCommand = 'w'
                print("w pressed! cut fwd")
                forward(ser1,speedCommand)
                headingMet = True
            #forward fast
            if inputCommand == 'W' or directionCommand == 'W':
                directionCommand = 'W'
                print("make this into a gps guided 'straight' heading?")
                forward(ser1,speedCommand)
            #reverse
            if inputCommand == 's' or directionCommand == 's':
                directionCommand = 's'
                reverse(ser1)
            #right
            if inputCommand == 'd' or directionCommand == 'd':
                directionCommand = 'd'
                sharpTurnRight(ser1)
            #left    
            if inputCommand == 'a' or directionCommand == 'a':
                directionCommand = 'a'
                sharpTurnLeft(ser1)
            #right-gradual (circle?) a is rightmtr, b is left.  a-fwd, b-less-fwd
            if inputCommand == 'e' or directionCommand == 'e':
                directionCommand = 'e'
                gradualTurnRight(ser1, speedCommand)
            #left-gradual (circle?) a is rightmtr, b is left.  b-fwd, a-less-fwd
            if inputCommand == 'q' or directionCommand == 'q':
                directionCommand = 'q'
                gradualTurnLeft(ser1, speedCommand)
            #set speed via keyboard
            if inputCommand == '1': 
                speedCommand = 1
            if inputCommand == '2': 
                speedCommand = 2
            if inputCommand == '3': 
                speedCommand = 3
            if inputCommand == '4': 
                speedCommand = 4
            if inputCommand == '5': 
                speedCommand = 5
            if inputCommand == 'x':
                print("Exiting! bye!")
                break
            if inputCommand == 'm' or cutCommand == 'm':
                cutCommand = 'm'
                print("turn off cut motor")
                ser2.write(str.encode('AE0\n'))
                reply = ser1.readline()
                print(reply)
            if inputCommand == 'M' or cutCommand == 'M':
                cutCommand = 'M'
                print("turn on cut motor")
                ser2.write(str.encode('AE1\n'))
                reply = ser2.readline()
                ser2.write(str.encode('A25\n'))
                reply = ser2.readline()
                print(reply)
            #non-planned chars:
            if inputCommand != 'M' and inputCommand != 'm' and inputCommand != 'w' and inputCommand != 'W' and inputCommand != 's' and inputCommand != 'd' and inputCommand != 'a' and inputCommand != 'q' and inputCommand != 'e' and inputCommand != '1' and inputCommand != '2' and inputCommand != '3' and inputCommand != '4' and inputCommand != '5'and inputCommand != 'g':
                #any non-planned characters - turn everything off.
                #first time through reset the start point so that it actually stops? simplefoc bug?
    
                cutCommand = 'o'
                directionCommand = 'o'
    
                ser1.write(str.encode('A0\n'))
                ser2.write(str.encode('A0\n'))
                reply = ser1.readline() + ser2.readline()
                time.sleep(.02) #idk if we need this.
                ser1.write(str.encode('B0\n'))
                reply = reply + ser1.readline()
                print(reply)
                dumpFaultState("key that is not wsda/g/M pressed, shutting off")
        else:
            print("stopped!!!")
            okToRun = False
            cutCommand = 'o'
            directionCommand = 'o'
            ser1.write(str.encode('A0\n'))
            ser2.write(str.encode('A0\n'))
            reply = ser1.readline() + ser2.readline()
            time.sleep(.2)
            ser1.write(str.encode('B0\n'))
            reply = reply + ser1.readline()
            ser1.write(str.encode('AE0\n'))
            ser2.write(str.encode('AE0\n'))
            reply = reply + ser1.readline() + ser2.readline()
            time.sleep(.2)
            ser1.write(str.encode('BE0\n'))
            reply = reply + ser1.readline()
            print(reply)
            
        loopCount = loopCount + 1
        time.sleep(0.5) #was 0.5
    
    #if we somehow get out of loop, turn off servo amps. 
    ser1.write(str.encode('A0\n'))
    ser2.write(str.encode('A0\n'))
    reply = ser1.readline() + ser2.readline()
    time.sleep(.2)
    ser1.write(str.encode('B0\n'))
    reply = reply + ser1.readline()
    ser1.write(str.encode('AE0\n'))
    ser2.write(str.encode('AE0\n'))
    reply = reply + ser1.readline() + ser2.readline()
    time.sleep(.2)
    ser1.write(str.encode('BE0\n'))
    reply = reply + ser1.readline()
    print(reply)


#movement and other functions:!!!!!!!!!!!!!!
def dumpFaultState(faultText):
    global faultMessageLogged, faultMessage
    if not faultMessageLogged:
        faultMessageLogged = True
        print(faultText)
        faultMessage = "Faulted: " + faultText + ". "#so that we can write fault message to the status file and display for user.
        global bumpers, lat, lon, gpsHeading, gpsVelocity, avgMagHeading, imuTemp, timeCurrentFix, batteryVoltage, estop, hac
        faultFile = open("/dev/shm/faults.log", "a")
        #faultFile.write(bumpers)
        #print(bumpers)
        faultFile.write(faultText)
        faultFile.write(f"\n Time: {timeCurrentFix:.1f}, Battery: {batteryVoltage:.2f}, Estop: {estop}, Bumpers: {bumpers}, Temp = {imuTemp:.1f}\n")
        faultFile.write(f"gps coords: {lat:.7f}, {lon:.7f}  gps heading: {gpsHeading:.1f} velocity: {gpsVelocity:.7f} magHeading: {avgMagHeading:.1f} Accuracy: {hac:.2f} \n")
        faultFile.close()

def clearFaultFile():
    faultFile = open("/dev/shm/faults.log", "w")
    faultFile.write("Can't control what you don't measure.\n\n")
    faultFile.close()

def forward(ser1, speedCommand):
    ser1.write(str.encode('AE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('BE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('A'+ str(4*speedCommand) + '\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('B'+ str(-4.4*speedCommand) + '\n'))
    reply = ser1.readline()
    print(reply)

def reverse(ser1):
    ser1.write(str.encode('AE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('BE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('A-10\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('B10\n'))
    reply = ser1.readline()
    print(reply)

#motorA is left, B is right. 
def sharpTurnRight(ser1):
    ser1.write(str.encode('AE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('BE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('A10\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('B10\n'))
    reply = ser1.readline()
    print(reply)

def sharpTurnLeft(ser1):
    ser1.write(str.encode('AE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('BE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('A-10\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('B-10\n'))
    reply = ser1.readline()
    print(reply)
    
def gradualTurnRight(ser1, speedCommand):
    ser1.write(str.encode('AE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('BE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode(f"A{10*speedCommand**0.8:.2f}\n"))
    reply = ser1.readline()
    print(reply)
    #ser1.write(str.encode('B'+ str(-6*speedCommand**0.8) + '\n'))
    ser1.write(str.encode(f"B{-6*speedCommand**0.8:.2f}\n"))
    reply = ser1.readline()
    print(reply)

def gradualTurnLeft(ser1, speedCommand):
    ser1.write(str.encode('AE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('BE1\n'))
    reply = ser1.readline()
    print(reply)
    #ser1.write(str.encode('A'+ str(6*speedCommand**0.8) + '\n'))
    ser1.write(str.encode(f"A{6*speedCommand**0.8:.2f}\n"))
    reply = ser1.readline()
    print(reply)
    #ser1.write(str.encode('B'+ str(-10*speedCommand**0.8) + '\n'))
    ser1.write(str.encode(f"B{-10*speedCommand**0.8:.2f}\n"))
    reply = ser1.readline()
    print(reply)

#A is left wheel. Correcting B polarity here for now. auto probably uses this function to drive always. 
#+values = fwd wheel rotation. - values = reverse.
#I can imagine for lots of path following or just gradual turning may want to change how hard we're turning. this allows that!
def manualTurn(ser1, lfSpeed, rtSpeed):
    ser1.write(str.encode('AE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('BE1\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('A'+ str(lfSpeed) + '\n'))
    reply = ser1.readline()
    print(reply)
    ser1.write(str.encode('B'+ str(-rtSpeed) + '\n'))
    reply = ser1.readline()
    print(reply)

#returns 1 if A1 < A2. wrap angle is the amount of the circle that is considered larger. 
    #(1 if A2 is more clockwise than A1)
def angleCompare(a1, a2, wrap):
    a1 = (a1 + 360)%360
    a2 = (a2 + 360)%360
    if ((a1 + wrap)%360) < wrap and a2 < (a1 + wrap)%360:
        return True
    elif ((a1 + wrap)%360) < wrap:
        return (a1 < a2)
    elif a2 > a1 + wrap:
        return False
    else:
        return (a1 < a2)
        
        
def setZone(zoneNum):
    print(f"attempting to set Zone to {zoneNum}\n")
    global shutdownWidth, north, south, east, west, zoneSet
    #choose which zone to run in:
    if zoneNum == 1:
        shutdownWidth = .000018 #5 digits 1.1m, 6 digits .11m 7 dig 0.01m 
        #He's faulting at .00001, changing to .000018, seems better maybe still faulting on downhill side
        north = yy.yyyyyy #was xx.xxxxxx
        south = yy.yyyyyy
        east = xx.xxxxxx # was xx.xxxxxx, added 2m or so to get closer to garden. Less negative is more east. More negative is more west.
        west = xx.xxxxxx
    #add more rectangles here! hahaha awesome.
    #south.garden:
    if zoneNum == 2:
        shutdownWidth = .000018 #5 digits 1.1m, 6 digits .11m 7 dig 0.01m 
        north = yy.yyyyyy
        south = yy.yyyyyy
        east = xx.xxxxxx
        west =  xx.xxxxxx #Should be xx.xxxxxx to overlap a tad with existing main area.    used xx.xxxxxx to cover zone 1. 
    #west.hill:
    if zoneNum == 3:
        shutdownWidth = .000018 #5 digits 1.1m, 6 digits .11m 7 dig 0.01m 
        north = yy.yyyyyy
        south = yy.yyyyyy #should be yy.yyyyyy but there is a skid steer/project. / I moved it waaay closer (yy.yyyyyy) 'cause dandelions.
        east = xx.xxxxxx
        west = xx.xxxxxx  #overlap a tad with existing area.
    #Deck
    if zoneNum == 4:
        shutdownWidth = .000018 #5 digits 1.1m, 6 digits .11m 7 dig 0.01m 
        north = yy.yyyy
        south =  yy.yyyy
        east =  xx.xxxxxx
        west =  xx.xxxxxx  
    zoneSet = 1
    
#apprently this fixes a definition order so you can write code later in a script but call it earlier? ugh. not too bad. 
if __name__=="__main__":
   main()