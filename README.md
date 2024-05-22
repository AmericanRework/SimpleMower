# SimpleMower
The best part is no part!  Here's a very raw but very simple automower in a single (1000 lines or less!) python file. (And some libraries/supporting threads, but the logic is all in one place, no hunting through 5 GB of code for one setting to change!) No husqvarna-dealer-only tools. No ROS. No app. Minimal complexity. No IDE - browser is all you need. This code has about 200 hours of mowing so far. I hope this helps keep automowers mowing instead of going to a landfill.


Mower Mechanical:
  - Husqvarna 450x automower. Mechanically they are pretty reliable. Dump the circuit boards and proprietary garbage but keep the sensors, motors, shell, and cutting hardware.
  - Automower drive motor PM: Now is a good time to regrease your 450 drive motor gearbox. 
Mower Electrical: 
  - Battery: use the two husqvarna batteries from your 450 automower. They include a 5s balance charger under the blue wrapper.
  - Use a DC current limited power supply for charging. I cap charger at 4 Amps - about 2A/battery, but still under the 5A / battery limit if one of the two batteries failed.
  - Brains + sensors + low power: Beaglebone Blue. Takes 12v and makes 5v and 3.3v for the RP2040 picos on the servo amps, as well as sensor power. Breadboard to break out the BBBlue digital inputs, and pull them up or down/ provide power to the hall-effect bump and lifted sensors.
  - Servo amp: Made our own: https://github.com/AmericanRework/Pico-2x-BLDC. Probably can use most simplefoc commander serial interface servo amps with minor modifications to code. Larger modifications to code and or electrical required for other serial or pwm controlled servo amps, but I believe the pwms are free on the BBBlue if that's the way you want to go. Current feedback, position feedback, future proofing, and heartbeat functions all argue for non-pwm servo amps with some sort of communication interface. 
  - Sparkfun RTK GPS to BBBlue usb port. (https://www.sparkfun.com/products/18292) 
  - I'll try to post prints and pinouts of all this. Use husqvarna battery + sensors + motors. Add BBBlue, RTK Gps, wiring harness, and servo amps.


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
  
