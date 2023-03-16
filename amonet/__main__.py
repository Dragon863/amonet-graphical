import struct
import traceback
import sys
import time

from amonet.common import Device
from amonet.handshake import handshake
from amonet.load_payload import load_payload
from amonet.logger import log

def flush_then_wait():
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(0.5)

def switch_boot0(dev):
    dev.emmc_switch(1)
    block = dev.emmc_read(0)
    if block[0:9] != b"EMMC_BOOT" and block[0:9] != b"BADD_BOOT":
        #dev.reboot()
        sys.stdout.write("what's wrong with your BOOT0?")

def flash_data(dev, data, start_block, max_size=0):
    while len(data) % 0x200 != 0:
        data += b"\x00"

    if max_size and len(data) > max_size:
        raise RuntimeError("data too big to flash")

    blocks = len(data) // 0x200
    for x in range(blocks):
        sys.stderr.write("[{} / {}]".format(x + 1, blocks))
        dev.emmc_write(start_block + x, data[x * 0x200:(x + 1) * 0x200])
    sys.stdout.write("")

def read_boot0(dev):
    switch_boot0(dev)
    i = 0
    with open('boot0.bin', 'wb') as fout:
        while True:
            data = dev.emmc_read(i)
            fout.write(data)
            i = i + 1
    
#  read data. note: number of bytes is increased to nearest blocksize
def dump_binary(dev, outfile, start_block, blockSize=0):
    initialBlocks = blockSize // 0x200
    initialStart = start_block
    counter = 0
    with open(outfile, "wb") as fout:
        while blockSize > 0:
            counter += 1
            data = dev.emmc_read(start_block)
            fout.write(data)
            start_block = start_block + 1
            blockSize = blockSize - 1
            if blockSize % 40 == 0:
                sys.stderr.write(
                    str(
                    (counter/initialBlocks)*100
                    )+"%"
                    )
                sys.stderr.write("Progress:"+str(((counter/initialBlocks)*100))+"\n")
                sys.stderr.flush()
            #sys.stdout.write("[{} / {}]".format(nblocks, initialBlocks), end='\r')

    
def flash_binary(dev, path, start_block, max_size=0):
    with open(path, "rb") as fin:
        data = fin.read()
    while len(data) % 0x200 != 0:
        data += b"\x00"

    sys.stdout.write(len(data))
    sys.stdout.write(max_size)
    if max_size and len(data) > max_size:
        raise RuntimeError("data too big to flash")

    blocks = len(data) // 0x200
    for x in range(blocks):
        sys.stderr.write("[{} / {}]".format(x + 1, blocks))
        dev.emmc_write(start_block + x, data[x * 0x200:(x + 1) * 0x200])
    sys.stdout.write("")

def switch_user(dev):
    dev.emmc_switch(0)
    block = dev.emmc_read(0)
    if block[510:512] != b"\x55\xAA":
        sys.stdout.write(str(block[510:512]))
        #dev.reboot()
        sys.stdout.write("There may be a problem with your GPT. It is probably safe to ignore this.")

def parse_gpt(dev):
    data = dev.emmc_read(0x400 // 0x200) + dev.emmc_read(0x600 // 0x200) + dev.emmc_read(0x800 // 0x200) + dev.emmc_read(0xA00 // 0x200)
    num = len(data) // 0x80
    parts = dict()
    for x in range(num):
        part = data[x * 0x80:(x + 1) * 0x80]
        part_name = part[0x38:].decode("utf-16le").rstrip("\x00")
        part_start = struct.unpack("<Q", part[0x20:0x28])[0]
        part_end = struct.unpack("<Q", part[0x28:0x30])[0]
        parts[part_name] = (part_start, part_end - part_start + 1)
        pass
    return parts

def main():
    sys.stdout.write("Please short the emmc as instructed in the article or readme whilst plugging in the usb cable")
    flush_then_wait()
    while True:
        try:
            dev = Device()
            dev.find_device()

            # 0.1) Handshake
            handshake(dev)
        except RuntimeError:
            log("wrong handshake response, probably in preloader")
            continue
        sys.stdout.write("handshake success!")
        flush_then_wait()
        break

    # 0.2) Load brom payload
    load_payload(dev, "brom-payload/build/payload.bin")

    # 1) Sanity check GPT
    log("Check GPT")
    switch_user(dev)

    # 1.1) Parse gpt
    gpt = parse_gpt(dev)
    sys.stdout.write("Partitions:")
    sys.stdout.write(str(gpt))
    sys.stdout.write(" ")
    flush_then_wait()
    if "lk_a" not in gpt or "tee1" not in gpt or "boot_a" not in gpt or "misc" not in gpt:
        sys.stdout.write("There may be an issue with your GPT. If the partitions shown above have readable names, it is safe to continue. Press the OK button to proceed...")
        flush_then_wait()
        input()
    
    sys.stdout.write("Do you want to dump the userdata partition (with wifi information in) or system partition?")
    sys.stdout.write("Option 1 = system\n")
    sys.stdout.write("Option 2 = userdata\n")
    sys.stdout.write("Option 3 = custom partition\n")
    sys.stdout.flush()
    part = input()
    if part == '1':
        sys.stdout.write("Warning: this process can take a LONG time. I recommend leaving this running overnight. Press the OK button to proceed...")
        input()
        sys.stdout.write("Writing contents of system_a to system.img...")
        sys.stdout.flush()
        dump_binary(dev, "system.img", gpt["system_a"][0], gpt["system_a"][1] * 0x200)
    elif part == '2':
        sys.stdout.write("Warning: this process can take a LONG time. I recommend leaving this running overnight. Press the OK button to proceed...")
        input()
        sys.stdout.write("Writing contents of userdata to userdata.img...")
        sys.stdout.flush()
        dump_binary(dev, "userdata.img", gpt["userdata"][0], gpt["userdata"][1] * 0x200)
    elif part == '3':
        sys.stdout.write("Which partition do you want to dump?")
        part = input(">> ")
        sys.stdout.write("Warning: this process can take a LONG time. I recommend leaving this running overnight. Press the OK button to proceed...")
        input()
        sys.stdout.write(f"Writing contents of {part} to {part}.img...")
        sys.stdout.flush()
        try:
            dump_binary(dev, f"{part}.img", gpt[part][0], gpt[part][1] * 0x200)
            sys.stdout.write("Partition dump complete!")
        except Exception as e:
            sys.stdout.write("Sorry, an error occurred dumping that partition. Please check that its name is spelt correctly. Press the OK button to view error...")
            flush_then_wait()
            input()
            traceback.sys.stdout.write_exc()

    exit("Execution ended.")


if __name__ == "__main__":
    main()