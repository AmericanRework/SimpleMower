

Assembly instuction + Suggested build/configuration order:
0. Take a look at all the documentation, decide if you really want to do this. ElectricalDoc.jpg has pinouts of various stuff that should be helpful.

1. Tear down your automower. Check the batteries, motors, gearboxes, etc... Make sure both batteries hold a charge (should be between 18 and 21v but might dip below if it's been off for a long time) 

   Automower motor/gearbox PM: The grease dries out and gets dirt in them. Plenty of videos on the web of how to clean out a and re-grease a gearbox. Here's the part I've yet to see anywhere else: while you're in the gearbox, take a very careful look at the drive motors. Mine were packed full of dirt and dried grease - they did not spin very freely. This may have actually been the reason their servo amp board kept dying. But it's not like I have any way to check that with their closed dealer-only-ecosystem! I (carefully!) pulled my motors apart (requires angle grinding the steel crimped tabs on back of motor / cracking entire shell of motor so you can unplug them from the servo amp) and washed all the old gunk out then re-assembled. I bet a solvent soak then maybe an oil bath to ensure motor bearings have at least some lubrication and rust protection could free up a stuck drive motor without cutting the motor apart.

2. Select and build/design/buy a servo amp or ESC or whatever. Get it spinning the automower motors. If it helps, the Pico-2x-BLDC linked earlier has pinouts for the automower motor plugs. Put a new plug on cut motor so it matches the drive motors. Get a BBBlue (or other sbc) and ensure you can control the three automower bldc motors (2x drive and 1x cut) from a python script running on your linux based SBC / rover controller.

3. Most of the risk is out by this point - If you're still serious and your servo amps are working, time to go shopping. Buy: BBBlue (-or other rover-brain- you should have this from previous step), Bench power supply or 5s charger capable of 21v, DC-DC converter (21 v in, 12v out, I think BBBlue wants a couple amps but I don't remember what it pulls), assortment kit of goofy tiny IO plugs for beaglebone blue, Molex 2 and 4 pin kit?, at least a couple feet of 14 gauge wire, 10A inline fuses and holders, I like the automotive fuses but whatever floats ya, A solderable breadboard and various resistors for your input/IO board. 

  3.5 May also want to buy RTK stuff now, I chose to buy it later once I had a working mower base. 

4. Move or buy a router so that your entire backyard has decent wifi coverage. We are literally sending like a few characters back and forth - don't need high bandwidth, but do need wifi over anywhere you want to control your robot.

5. RTK stuff: You can make it work remote control with just the stuff above. If you are close to an existing rtk base station(http://rtk2go.com/)  you may only need one rtk setup. I decided to run my own rtk base station so I needed 2x of these: https://www.sparkfun.com/products/18292. I ran the base station from a beaglebone black but a rasberry pi or pretty much anything that is running linux and is on all the time and is near your antenna location should work. Obviously if you use your own base station that will also need a static IP adress from your router.

6. Load your BBBlue image (link!?) then get the BBBlue on whatever your backyard wifi will be with a static address. Log in, do some updates, make sure your image is good and stuff is working. Decide how much you trust randos on the internet and your own build skills (you shouldn't) so plug in the servo amp(s) to the BBBlue for some bench testing. Confirm BBBlue can control motors through whatever servo amp you chose.

   Most of the code has setup or install instructions in the top few lines.

7. BBBlue IO breakout board. Connect at least the bump sensors and estop button to an io breakout board for the BBBlue. I'd also suggest the battery level sensor right now as well 'cause you're right there and it gets harder to do after everything is in the robot. Test all the pins and sensors.

8. Make a 21v wiring harness and get a DC-DC converter to make 12v from battery 18-21v. I used molex plugs on my wiring harness that match the automower battery plugs to make it easy to disconnect stuff. Fuses on each battery line is a good idea. Make sure your batteries are at the same voltage when you plug them both in. You could make a whole battery integration board and include low battery voltage shutoff but simple is a good starting place. So we've got simple. My 'harness' had: 6x 21v connections: 1. (fused) Battery 1. 2. (fused) Battery 2. 3. DC-DC 21 down to 12v. 4. Charger input. 5. servo amp: drive motors. 6. servo amp: cut motors.

   Modify the charging dock: throw out their board and loop signal generator. Hook up your ~4a 21v current limited power supply directly to the +/- leads of the dock charging connectors.
   
9. At this point you can load up the code here and mow remotely with your automower, but no GPS. 

   For a beaglebone with cloud9: just copy the files in the rover directory here to your beaglebone. Install couple libraries, again, see the top of any code file for any relevant install instructions. Start TobyAuto, TobyWebserver (comment out the gps lines if you are not using gps) and you have a remote rover. Setup a base station then run RTK_Example to get rtk gps coords written to a file and enable auto mode.

   How to drive: wsda. q and e are gradual turns. 'M' starts the mower. m stops the mower. 12345 are speed, and any other key stops everything immediately. g is auto mode and won't work if you don't have gps.

10. Setup the magnetometer. This... ugh. This code is mostly garbage. It works to maybe 45 degrees? I'm sure I could go find a better magnetometer calibration routine but I have a suspicion that the magnetometer is too close to the motors and is picking up fields from them. You'll probably need to point your robot in various directions (N/S/E/W/NW/SW/NE/SE) and make your own magnetometer function. Plot the raw magnetic field values in excel then create a function from there. 

11. RTK config: Figure out your base antenna location if you're running a base station. And I mean down to the cm. The more accurate the better. Put those known coordinates into your base station config, and then start the base station server from command line. 

  11.5 RTK contd: Back to the rover. Mount rtk antenna to top of mower. Drill a hole somewhere sensible on automower, route GPS antenna cable, then hot glue around the cable so no water or dust gets into the mower. I hot glued antenna metal baseplate to top of mower and stuck antenna to that. Start the rover GPS script (rtk_example.py) and you should fairly quickly see a sub 2cm horizontal accuracy dumped to /dev/shm/coords.txt.

12. At this point, you can start the gps thread (rtk_example.py), the javascript server thread (MyTobyServer.js), and the robot control loop(TobyAuto1.2.py). Hit the ip address of the mower (w.x.y.z:8001) in your pc web browser and you should see a 'remote control' screen. Drive the rover/mower around your yard and find the lat/lon coordinates of some rectangles you want to mow. Put the coordinates into the setZone function.

13. Drive into a rectangle, press whatever zone number that is on your keyboard (yes 12345 are usually speed but for gps mode we use 12345 to set zone#, speed is overridden in gps mode), then hit g and it'll start mowing automatically.





Additional ideas:
  - You could probably hook up the DC motor on cut height to the BBBlue dc motor drivers if you actually care about cut height. I set it as high as possible so we don't get stuck. I haven't touched it ever since. One more thing to fail.
  - Brackets? nah. Hot glue everything into the automower. If the hot glue breaks, use more glue. So far so good, but not sure how this will hold up in the long run lol... If someone wants to design real mounting brackets that'd be cool but so far does not appear neccesary. heh. Hot glue FTW.
