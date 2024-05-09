# SimpleMower
The best part is no part!  Here's a very raw but very simple automower in a (1000 lines or less!) python file. Yes there are some libraries and extras to setup/install but no chasing a rabbit through a dozen files and spending hours recompiling or uploading when you want to modify, improve, or extend. No boundary wire. No husqvarna-only tools. No ROS. No app. No screen. Minimal complexity. This is working mowing rectangles into a lawn right now.

Mower Mechanical:
Husqvarna automower 450. Mechanically they are pretty awesome. Electrically. Well. Their electrical is better than their software, but after ~6 or 7 years we started having problems with the main control board.

Mower Electrical: 
  - Battery: use the two husqvarna batteries from your 450 automower. They include a 5s balance charger under the blue wrapper. I made a quick and dirty wiring harness: fuse and split the 21v out to: dc-dc down to 12v for the servo amp control voltage and beaglebone blue power input. Use a DC current limited power supply for charging. I cap mine at 4 Amps to charge so about 2A/battery.
  - Brains + sensors + low power: Beaglebone Blue. Takes 12v and makes 5v and 3.3v for the RP2040 picos on the servo amps, as well as sensor power. Breadboard to break out the BBBlue digital inputs, and pull them up or down/ provide power to the hall-effect bump and lifted sensors.
  - Servo amp: Read all about it here. Probably works with any serial capable simplefoc servo amp and a bit of setup/modification.
  - Sparkfun RTK GPS to BBBlue usb port.

Mower Sensors:
  - RTK GPS: SEMU consulting are my hero.
  - Bump, lifted, and estop are all from the automower.

RTK Base station:
  - Beaglebone Black + Sparkfun RTK GPS kit + SEMU Consulting again.

Mower Software:
  - mows rectangles that are straight up gps coords.
  - 
