# MountWizzard <img src="docu/pics/mw.png" width='64' height='64'/>

#### Application for use in 10micron Mount environment
Supports SGPro, TheSkyX, Stickstation, MBox, UniHedron SQR, OpenWeather and some more ASCOM parts
(C) Michael Würtenberger 2016, 2017

#### Version release: 2.4, test version actual 2.5.22 beta

[Link to the extended documentation and handbook of MountWizzard](./docu/home.md)

## Features:
- Imaging Software: Sequence Generator Pro and TheSkyX are supported. Please refer to their homepages for use.
- Blind solve for base points. All options of imaging Software is accepted.
- Generate model point track for observing objects for modeling along track
- Optimize model (even when model was done manually)
- Auto refraction - even when not slewing, checking IDLE times of camera
- A lot of settings of mount visible and changeable
- Pointing display ra/dec az/alt at the same time
- Define up to 6 mount positions, which could be slew directly (e.g. flat panel, check ccd etc.)
- Getting data from open weather (API key needed) and Stickstation
- Set tracking on/off, set dual tracking on/off, set tracking speed Sideral / Lunar / Solar
- Driver stays always in sync aligns model (no model change through sync), or use direct IP
- Analyse modeling data with separate plots.
- Modeling chart with meridian flip information

## Usage:
Please setup SGPro / TheSkyX as you would image. Please also do some sort of focusing (should be obvious) and test some images
before start. If you would like to speed-up the modeling, please disable in SGPro star analysis. It takes 4-5 s per
image in addition.

There is an entry for dome support. If you don't hav a dome to slew, please ensure, that there is no driver selected.
This is indicated, that the DOME status on top of the window in grey. You can disable the dome driver under settings
by calling the ASCOM chooser for dome an in the selection window upcoming just press "Cancel". This should disable the
driver.

### There were some videos for installation and first use out:
The Application could be found under /dist on github.

Installation of MountWizzard: https://www.youtube.com/watch?v=GX0H6ddq0KM

Update to new version: https://www.youtube.com/watch?v=KduOp2mn0N8

Make a new mount model: https://www.youtube.com/watch?v=nCQLErKP-yo

Imaging with SGPro: https://www.youtube.com/watch?v=9mA4qxPaE-8

Make model along DSO path: https://www.youtube.com/watch?v=KhVvuXzNezE

Direct Mount Connection via IP: https://youtu.be/JmdhXn4ZDlE

Download Orbital Elements and UTC Data for mount update: https://youtu.be/U4dty-PMXLo

Another First Use Video: https://youtu.be/JMAfZoq8rBI

If you have any hints / bugs / feature requests, please let me know. Right location is 10micron forum under
the software section: http://www.10micron.eu/forum/viewforum.php?f=18&sid=ae4c89d5d18adb85c3e9d32c26fba2f4
If you have found bugs (especially in the beta stage), please add the mount.YYYY-MM-DD.log file and post it
to the forum. This would help me a lot.

### Finally
The use this software is at your own risk! No responsibility for damages to your mount or other equipment or your
environment. Please take care yourself !

Hope this makes fun and helps for your hobby, CS Michel
