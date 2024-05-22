Basic architecture: 
  - javascript webserver serves out page that has a script that uses fetch to write commands to the robot. Commands are written to a file in shared memory (dev/shm/keyCommands.txt) which are then picked up by the robot control loop. (Rely on filesystem for mutex. No idea if that's safe but if you have 15 people trying to control your robot from the web you might be doing something wrong. You want to write to ram so you're not hammering writes into flash memory.) The control loop in turn writes a status file that is dumped into the reply by the webserver and returned to the client as part of the fetch.
  - Robot control loop runs twice a second, checking for stuff like over-current, bumping into obstacles etc... and stops if any of these reasons to fault are met. Control loop then reads an input key from the webserver remote control, then assigns servo amp desired velocity. Faults are temporarily reset by a user attempting to drive in a new direction, but if the fault condition is still on in 5 seconds, it'll stop again.
  - One of the driving modes is 'g' for gps mode! If you press g, we use a simple auto mode where we start checking gps coordinate boundaries vs our current position and if you get close to a boundary we spin around and head back the other way. Robot will full stop if it exceeds the boundary limit. Faults and machine status are logged to file (/dev/shm/status.txt) which is displayed by the webserver. 
  - RTK is it's own thread that writes to /dev/shm/coords.txt when it gets an update. Robot control loop grabs the latest position fix from that file. Control loop can then determine if you're stuck or if you've stopped getting gps updates. RTK base station is on a beaglebone black.
  