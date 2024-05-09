# SimpleMower
The best part is no part!  Here's a very raw but very simple automower in a single (1000 lines or less!) python file. No husqvarna-dealer-only tools. No ROS. No app. Minimal complexity. No IDE - browser is all you need. This code has about 100 hours of mowing so far. I hope this helps keep automowers mowing instead of going to a landfill.


Mower Mechanical:
  - Husqvarna automower 450. Mechanically they are pretty reliable. Electrically. Well. Their electrical is better than their software, but after ~6 or 7 years we started having problems with the main control board and the charging board. The included power supply died after 1 or 2 years and they wanted $200 for a new one. hahaha. Nope. Tear everything electrical out except the motors and start over.
  - Automower drive motor PM: Now is a good time to regrease your 450 drive motor gearbox. The grease dries out and gets dirt in it. Here's the part I've yet to see anywhere else: while you're in the gearbox, Look at the drive motors. Mine were packed full of dirt and dried grease - they did not spin very freely. I carefully pulled my motors apart (requires angle grinding the steel crimped tabs on back of motor / cracking entire shell) and washed all the old gunk out then re-assembled but I bet a solvent soak then maybe an oil bath to ensure motor bearings have at least some lubrication and rust protection could free up a stuck bldc motor.)
  - You could probably hook up the DC motor on cut height to the BBBlue if you actually care. I set it as high as possible so we don't get stuck. I haven't touched it ever since. One more thing to fail.

Mower Electrical: 
  - Battery: use the two husqvarna batteries from your 450 automower. They include a 5s balance charger under the blue wrapper. I made a quick and dirty wiring harness: fuse and split the 21v out to: dc-dc down to 12v for the servo amp control voltage and beaglebone blue power input. Use a DC current limited power supply for charging. I cap mine at 4 Amps to charge so about 2A/battery, but still under the 5A / battery limit if one of the two batteries failed.
  - Brains + sensors + low power: Beaglebone Blue. Takes 12v and makes 5v and 3.3v for the RP2040 picos on the servo amps, as well as sensor power. Breadboard to break out the BBBlue digital inputs, and pull them up or down/ provide power to the hall-effect bump and lifted sensors.
  - Servo amp: Made our own: https://github.com/AmericanRework/Pico-2x-BLDC. Probably can use most simplefoc commander serial interface servo amps with minor modifications. Larger modifications required for other serial or pwm controlled servo amps, but I believe the pwms are free on the BBBlue if that's the way you want to go. Current feedback, position feedback and heartbeat functions all argue for non-pwm servo amps. 
  - Sparkfun RTK GPS to BBBlue usb port. Drill a hole somewhere on automower, route GPS antenna cable, then hot glue around the cable so no water or dust gets into the mower. Hot glue antenna metal baseplate to top of mower.
  - I'll try to post prints and pinouts of all this. Use husqvarna battery + sensors + motors. Add BBBlue, RTK Gps, wiring harness, and servo amps. 

Mower Sensors:
  - RTK GPS: SEMU consulting are my hero.
  - Bump, lifted, and estop are all from the automower. They are hall effect sensors. I'll try to post their pinouts as well. Steal the plugs from your automower mainboard using a heat gun. Hot glue backside of the connector. 
  - Temp, magnetometer, (accelermoeter) and battery level are done by BBBlue. Battery level is a resistor voltage divider to the BBBlue ADC.

RTK Base station:
  - Beaglebone Black + Sparkfun RTK GPS kit + SEMU Consulting again.

Mower Software:
  - Remote control from your browser. Hit the IP address of the Beaglebone Blue, get a remote control interface. No images from the mower but you could probably add that.
  - Yes you can restart it remotely. Look at mower out your window, see it's good, read error message on remote webpage, restart or take appropriate action.
  - mows rectangles that are aligned with gps latitude and longitude. I have 4 rectangular zones that comprise about 70% of my yard. Yes you still have to get out a mower for the edges. You're not going to like whatever algorithm I come up with for mowing your lawn so write that part yourself - it's the fun part! And I know you still have your old manual mower 'cause your husqvarna broke at least once a year and took forever to fix/get parts.
  - It doesn't know how to find a charger, follow a vector, mow a pattern, mow non-rectangular shapes, have exclusion areas, or get close to an edge/etc... That should be the next version though I'm not sure how long that'll take.
