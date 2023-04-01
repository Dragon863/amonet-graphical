# amonet

This is a modified graphical version of the amonet exploit by `xyzz` (https://github.com/xyzz/amonet) ported to the amazon biscuit (all credit for the original exploit goes to xyzz!). This tool will allow you to dump the internal emmc memory, and extract data from the device.
If you are compiling this yourself, before running `__init__.py` for the first time be sure to run `setup.sh` to compile binaries for the payloads.
- Before running, peel off the rubber grip on the base of the device and use a torx 8 screwdriver to dissasemble the device and expose the main board. After this, use a flat head screwdriver or thin plastic tool to pry off the RF shield on the main processor board. 
- You will the need a small metal piece such as a very small flat head screwdriver or a piece of tin foil to short circuit the capacitor next to the eMMC in the area shown below.
![image](https://i.imgur.com/2MkRyF6.jpeg)
- Once you have clicked start on the program, follow the instruction above and plug in the usb with the short circuit still in place.
- The filesystem will be extracted to a .img file which can be mounted on linux, or extracted using decompression software on windows. The wifi config file is located in `/misc/wifi` on the userdata partition and spotify credentials are in `/system/etc/AlexaClientSDKConfig.json` on the system partition. (these are as of fireOS 6.5.5.5)
