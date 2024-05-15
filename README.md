# SimpleMower
The best part is no part!  Here's a very raw but very simple automower in a single (1000 lines or less!) python file. (And some libraries/supporting threads, but the logic is all in one place, no hunting through 5 GB of code for one setting to change!) No husqvarna-dealer-only tools. No ROS. No app. Minimal complexity. No IDE - browser is all you need. This code has about 100 hours of mowing so far. I hope this helps keep automowers mowing instead of going to a landfill.


Mower Mechanical:
  - Husqvarna 450x automower. Mechanically they are pretty reliable. Dump the circuit boards and proprietary garbage but keep the sensors, motors, shell, and cutting hardware.
  - Automower drive motor PM: Now is a good time to regrease your 450 drive motor gearbox. Put this into assembly instruction: The grease dries out and gets dirt in it. Here's the part I've yet to see anywhere else: while you're in the gearbox, take a very careful look at the drive motors. Mine were packed full of dirt and dried grease - they did not spin very freely. I carefully pulled my motors apart (requires angle grinding the steel crimped tabs on back of motor / cracking entire shell) and washed all the old gunk out then re-assembled but I bet a solvent soak then maybe an oil bath to ensure motor bearings have at least some lubrication and rust protection could free up a stuck bldc motor.)
  - You could probably hook up the DC motor on cut height to the BBBlue if you actually care. I set it as high as possible so we don't get stuck. I haven't touched it ever since. One more thing to fail.

Mower Electrical: 
  - Battery: use the two husqvarna batteries from your 450 automower. They include a 5s balance charger under the blue wrapper.
  - this also in assembly instruction: make wiring harness: fuses and split the 21v out to: dc-dc down to 12v, charging, and servo amps. Use a DC current limited power supply for charging. I cap charger at 4 Amps - about 2A/battery, but still under the 5A / battery limit if one of the two batteries failed.
  - Brains + sensors + low power: Beaglebone Blue. Takes 12v and makes 5v and 3.3v for the RP2040 picos on the servo amps, as well as sensor power. Breadboard to break out the BBBlue digital inputs, and pull them up or down/ provide power to the hall-effect bump and lifted sensors.
  - Servo amp: Made our own: https://github.com/AmericanRework/Pico-2x-BLDC. Probably can use most simplefoc commander serial interface servo amps with minor modifications to code. Larger modifications to code and or electrical required for other serial or pwm controlled servo amps, but I believe the pwms are free on the BBBlue if that's the way you want to go. Current feedback, position feedback, future proofing, and heartbeat functions all argue for non-pwm servo amps with some sort of communication interface. 
  - Sparkfun RTK GPS to BBBlue usb port. (https://www.sparkfun.com/products/18292) (assmbly instruction:)Drill a hole somewhere sensible on automower, route GPS antenna cable, then hot glue around the cable so no water or dust gets into the mower. Hot glue antenna metal baseplate to top of mower.
  - I'll try to post prints and pinouts of all this. Use husqvarna battery + sensors + motors. Add BBBlue, RTK Gps, wiring harness, and servo amps.
  - assembly: Hot glue everything into the automower. If the hot glue breaks, use more glue. So far so good, but not sure how this will hold up in the long run lol... If someone wants to design real mounting brackets that'd be cool but so far does not appear neccesary. heh. Hot glue FTW.

Mower Sensors:
  - RTK GPS: SEMU consulting are my hero. (https://github.com/semuconsulting) We use two of their libraries, but you might also use their open source linux GUI for just testing out the ZED-F9P hardware at first.
  - Bump, lifted, and estop are all from the automower. They are hall effect sensors. I'll try to post their pinouts as well. Steal the plugs from your automower mainboard using a heat gun. Hot glue backside of the connector. 
  - Temp, magnetometer, (accelermoeter) and battery level are done by BBBlue. Battery level is a resistor voltage divider to the BBBlue ADC.

RTK Base station:
  - Beaglebone Black + Sparkfun RTK GPS kit + SEMU Consulting again.

Mower Software:
  -  Remote control from your browser. Hit the IP address of the Beaglebone Blue, get a remote control interface. No camera on the mower but you could probably add that.
  - Yes you can restart it remotely. Look at mower out your window, see it's good, read error message on remote webpage, restart or take appropriate action.
  - Mows rectangles that are aligned with gps latitude and longitude. I have 4 obstacle free rectangular zones that comprise about 70% of the yard. Yes you still have to get out a manual mower for the edges. You're not going to like whatever algorithm I come up with for mowing your lawn so write that part yourself - it's the fun part! (though if you wait long enough I'll post my solution)
  - Robot doesn't yet know how to find a charger, follow a vector, mow a pattern, mow non-rectangular shapes, have exclusion areas, back up after bonking into something, slow down near an edge/etc... Working on it, will update once I'm happy with it.

    
Code readme: 
  - Basic architecture: javascript webserver serves out page that has a script that uses fetch to write commands to the robot. Commands are written to a file in shared memory (dev/shm) which are then picked up by the robot control loop. (Rely on filesystem for mutex. No idea if that's safe but if you have 15 people trying to control your robot from the web you might be doing something wrong. You want to write to ram so you're not hammering writes into flash memory.) The control loop in turn writes a status file that is dumped into the reply by the webserver and returned to the client as part of the fetch.
  - Robot control loop runs twice a second, checking for stuff like over-current, bumping into obstacles etc... and stops if any of these reasons to fault are met. Control loop also reads an input key from the webserver remote contorl. Faults are temporarily reset by a user attempting to drive in a new direction, but if the fault is still on in 5 seconds, it'll stop again. One of the driving modes is 'g' for gps mode! If you press g, we use a simple auto mode where we start checking gps coordinate boundaries vs our current position and if you get close to a boundary we spin around and head back the other way. Robot will full stop if it exceeds the boundary limit. Faults and machine status are logged to file.  
  - RTK is it's own thread that writes to /dev/shm when it gets an update. Robot control loop grabs the latest position fix from that file. Control loop can then determine if you're stuck or if you've stopped getting gps updates. RTK base station is on a beaglebone black.
  

Assembly instuction:
Suggested build/configuration order:
1. Tear down your automower. Check the batteries, motors, gearboxes, etc... Make sure both batteries hold a charge (should be between 18 and 21v but might dip below if it's been off for a long time) I made up a quick and dirty charging cable for the automower batteries - Just dump up to 4A (technically 5A but let's be a little safe? No idea on a 430 automower if this all works I think the main difference is one less battery pack so probably works great) down the red and black of the battery cables that works to charge a battery using the stock balance charger even if it's out of the robot.
2. Select and build/design/buy a servo amp or ESC or whatever. Get it spinning the automower motors. If it helps, the Pico-2x-BLDC linked earlier has pinouts for the automower motor plugs. Put a new plug on cut motor so it matches the drive motors.
3. Most of the risk is out by this point - If you're still serious and your servo amps are working, time to go shopping. Buy: BBBlue, Bench power supply or 5s charger capable of 21v, DC-DC converter (21 v in, 12v out, I think BBBlue wants a couple amps but I don't remember what it pulls), assortment kit of goofy tiny IO plugs for beaglebone blue, Molex 2 and 4 pin kit?, at least a couple feet of 14 gauge wire, 10A inline fuses and holders, I like the automotive ones but whatever floats ya, A solderable breadboard and various resistors for your input/IO board. Move or buy a router so that your entire backyard has decent wifi coverage. We are literally sending like a few characters back and forth - don't need high bandwidth, but do need wifi over anywhere you want to drive your robot.
4. RTK stuff: You can make it work remote control with just the stuff above. If you are close to an existing rtk base station(https://rtk2go.com/) you may only need one rtk setup. I decided to run my own rtk base station so I needed 2x of these: https://www.sparkfun.com/products/18292. I ran the base station from a beaglebone black but a rasberry pi or pretty much anything that is running linux and is on all the time and is near your antenna location should work. Obviously if you use your own base station that will also need a static IP adress from your router.
5. Load your BBBlue image (link!?) then get the BBBlue on whatever your backyard wifi will be with a static address. Log in, do some updates, make sure your image is good and stuff is working. Decide how much you trust randos on the internet and your own build skills (you shouldn't) so plug in the servo amp(s) to the BBBlue for some bench testing. Confirm BBBlue can control motors through whatever servo amp you chose.
6. BBBlue IO breakout board. Connect at least the bump sensors and estop button to an io breakout board for the BBBlue. I'd also suggest the battery level sensor right now as well 'cause you're right there and it gets harder to do after everything is in the robot. Test all the pins and sensors.
7. Make a 21v wiring harness and get a DC-DC converter to make 12v. I used molex plugs that match the automower battery plugs to make it easy to disconnect stuff. Fuses on each battery line is a good idea. Make sure your batteries are at the same voltage when you plug them both in. You could make a whole battery integration board and include low battery voltage shutoff but simple is a good starting place. So we've got simple. My 'harness' had: 6x 21v connections: 1. (fused) Battery 1. 2. (fused) Battery 2. 3. to DC-DC. 4. to Charger input. 5. to servo amp drive motors. 6. servo amp cut motors.
8. At this point you can load up the code here and mow remotely with your automower but no GPS. wsda. q and e are gradual turns. 'M' starts the mower. m stops the mower. 12345 are speed, and any other key stops everything immediately. G is auto mode and won't work if you don't have gps.
9. Setup the magnetometer. This... ugh. This code is mostly garbage. It works to maybe 45 degrees? I'm sure I could go find a better magnetometer calibration routine but I have a suspicion that the magnetometer is too close to the motors and is picking up fields from them. You'll probably need to point your robot in various directions (N/S/E/W/NW/SW/NE/SE) and make your own magnetometer function. Plot the raw magnetic field values in excel then create a function from there. 
10. RTK config: Figure out your antenna location if you're running a base station. And I mean down to the cm. The more accurate the better. Put those known coordinates into your base station config, and then start the base station server from command line. Back to the rover and Start the rover GPS script and you should fairly quickly see a sub 2cm horizontal accuracy.
11. At this point, start the gps thread, the javascript server thread, and the robot control loop. Hit the ip address of the mower (@ port 8001) and you should see a 'remote control' screen. Drive the rover/mower around your yard and find the lat/lon coordinates of some rectangles you want to mow. Put the coordinates into the setZone function.
12. Drive into a rectangle, press whatever zone number that is on your keyboard (yes 12345 are usually speed but for gps mode we use 12345 to set zone#, speed is overridden in gps mode), then hit g and it'll start mowing automatically.

