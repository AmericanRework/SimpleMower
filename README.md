# SimpleMower
The best part is no part!  Here's a very raw but very simple automower in a single (1000 lines or less!) python file. (And some libraries/supporting threads, but the logic is all in one place, no hunting through 5 GB of code for one setting to change!) No husqvarna-dealer-only tools. No ROS. No app. Minimal complexity. No IDE - browser is all you need. This code has about 100 hours of mowing so far. I hope this helps keep automowers mowing instead of going to a landfill.


Mower Mechanical:
  - Husqvarna 450x automower. Mechanically they are pretty reliable. The bump sensors, motors, seals, and batteries have been good. Electrically on a single mower we've had: 2x mainboards die($300 each), 1x power supply ($200), and 1x charging board/loop sensor($..? this was the last straw.) So dump the controls but keep the sensors, motors, shell, and cutting hardware.
  - Automower drive motor PM: Now is a good time to regrease your 450 drive motor gearbox. The grease dries out and gets dirt in it. Here's the part I've yet to see anywhere else: while you're in the gearbox, Look at the drive motors. Mine were packed full of dirt and dried grease - they did not spin very freely. I carefully pulled my motors apart (requires angle grinding the steel crimped tabs on back of motor / cracking entire shell) and washed all the old gunk out then re-assembled but I bet a solvent soak then maybe an oil bath to ensure motor bearings have at least some lubrication and rust protection could free up a stuck bldc motor.)
  - You could probably hook up the DC motor on cut height to the BBBlue if you actually care. I set it as high as possible so we don't get stuck. I haven't touched it ever since. One more thing to fail.

Mower Electrical: 
  - Battery: use the two husqvarna batteries from your 450 automower. They include a 5s balance charger under the blue wrapper. I made a quick and dirty wiring harness: fuse and split the 21v out to: dc-dc down to 12v for the servo amp control voltage and beaglebone blue power input. Use a DC current limited power supply for charging. I cap mine at 4 Amps to charge so about 2A/battery, but still under the 5A / battery limit if one of the two batteries failed.
  - Brains + sensors + low power: Beaglebone Blue. Takes 12v and makes 5v and 3.3v for the RP2040 picos on the servo amps, as well as sensor power. Breadboard to break out the BBBlue digital inputs, and pull them up or down/ provide power to the hall-effect bump and lifted sensors.
  - Servo amp: Made our own: https://github.com/AmericanRework/Pico-2x-BLDC. Probably can use most simplefoc commander serial interface servo amps with minor modifications. Larger modifications required for other serial or pwm controlled servo amps, but I believe the pwms are free on the BBBlue if that's the way you want to go. Current feedback, position feedback and heartbeat functions all argue for non-pwm servo amps. 
  - Sparkfun RTK GPS to BBBlue usb port. (https://www.sparkfun.com/products/18292) Drill a hole somewhere sensible on automower, route GPS antenna cable, then hot glue around the cable so no water or dust gets into the mower. Hot glue antenna metal baseplate to top of mower.
  - I'll try to post prints and pinouts of all this. Use husqvarna battery + sensors + motors. Add BBBlue, RTK Gps, wiring harness, and servo amps.
  - Hot glue everything into the automower. If the hot glue breaks, use more glue. So far so good, but not sure how this will hold up in the long run lol... If someone wants to design real mounting brackets that'd be cool but so far does not appear neccesary. heh. Hot glue FTW.

Mower Sensors:
  - RTK GPS: SEMU consulting are my hero. (https://github.com/semuconsulting) We use two of their libraries, but you might also use their open source linux GUI for just testing out the ZED-F9P hardware at first.
  - Bump, lifted, and estop are all from the automower. They are hall effect sensors. I'll try to post their pinouts as well. Steal the plugs from your automower mainboard using a heat gun. Hot glue backside of the connector. 
  - Temp, magnetometer, (accelermoeter) and battery level are done by BBBlue. Battery level is a resistor voltage divider to the BBBlue ADC.

RTK Base station:
  - Beaglebone Black + Sparkfun RTK GPS kit + SEMU Consulting again.

Mower Software:
  -  Remote control from your browser. Hit the IP address of the Beaglebone Blue, get a remote control interface. No images from the mower but you could probably add that.
  - Yes you can restart it remotely. Look at mower out your window, see it's good, read error message on remote webpage, restart or take appropriate action.
  - Basic architecture: javascript webserver serves out page that has a script that uses fetch to write commands to the robot. Commands are written to a file in shared memory (dev/shm) which are then picked up by the robot control loop. (Rely on filesystem for mutex. No idea if that's safe but if you have 15 people trying to control your robot from the web you might be doing something wrong. You want to write to ram so you're not hammering writes into flash memory.) Robot control loop runs twice a second, checking for stuff like over-current, bumping into obstacles etc... and stops if any of these reasons to fault are met. Faults are reset by attempting to drive in a new direction, but if the fault is still on in 5 seconds, it'll stop again. One of the driving modes is 'g' for gps mode! if you press g, we use a simple auto mode where we start checking gps boundaries and if you hit one we spin around and head back the other way. Faults and machine status are logged to files. The status file is dumped into the reply by the webserver and returned as part of the fetch.
  - RTK is it's own thread that writes to /dev/shm when it gets an update. Robot control loop grabs the latest position fix. Control loop determines if you're stuck or if you've stopped getting gps updates. RTK base station is on a beaglebone black.
  - Mows rectangles that are aligned with gps latitude and longitude. I have 4 rectangular zones that comprise about 70% of my yard. Yes you still have to get out a mower for the edges. You're not going to like whatever algorithm I come up with for mowing your lawn so write that part yourself - it's the fun part! And I know you still have your old manual mower 'cause your husqvarna broke at least once a year and took forever to fix/get parts.
  - Robot doesn't yet know how to find a charger, follow a vector, mow a pattern, mow non-rectangular shapes, have exclusion areas, back up after bonking into something, slow down near an edge/etc... That should be in the next version though I'm not sure how long that'll take.


Suggested build/configuration order:


