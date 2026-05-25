import aiopjlink as pLink
import asyncio
import configparser
import os

config = configparser.ConfigParser()
ini_file_path = os.path.join(os.path.dirname(__file__), 'ipAddress.ini')

files_read = config.read(ini_file_path)
print("______________________________________")
print("File read:", files_read)

try:
    PJ1_ID = config['ipvalues']['PJ1']
    PWD1 = config['pwd']['PWD1']
except KeyError:
    print("Cannot find used key.")
    PJ1_ID = "0.0.0.0"
try:
    PJ2_ID = config['ipvalues']['PJ2']
    PWD2 = config['pwd']['PWD2']
except KeyError:
    print("Cannot find used key.")
    PJ2_ID = "0.0.0.0"
try:
    PJ3_ID = config['ipvalues']['PJ3']
    PWD3 = config['pwd']['PWD3']
except KeyError:
    print("Cannot find used key.")
    PJ3_ID = "0.0.0.0"
try:
    PJ4_ID = config['ipvalues']['PJ4']
    PWD4 = config['pwd']['PWD4']
except KeyError:
    print("Cannot find used key.")
    PJ4_ID = "0.0.0.0"

print("______________________________________")   
print("IP Address:")
print("PJ1", PJ1_ID)
print("PJ2", PJ2_ID)
print("PJ3", PJ3_ID)
print("PJ4", PJ4_ID)

print("______________________________________")
print("Creating Project 1 & setting password")
PJ1 = pLink.PJLink(PJ1_ID,PWD1)

print("Creating Project 2 & setting password")
PJ2 = pLink.PJLink(PJ2_ID,PWD2)

print("Creating Project 3 & setting password")
PJ3 = pLink.PJLink(PJ3_ID,PWD3)

print("Creating Project 4 & setting password")
PJ4 = pLink.PJLink(PJ4_ID,PWD4)
print("______________________________________")

async def PJ1Power():
        try:
            print("______________________________________")
            print("Attempting to wake PJ1.")
            await asyncio.wait_for(PJ1.power.turn_on(),timeout = 1.5)
            await asyncio.sleep(5)
            print("Errors from PJ1: ", await PJ1.errors.query())
        except asyncio.TimeoutError:
             print("PJ1 timed out, Check the configuration file?")

async def PJ2Power():
        try:
            print("______________________________________")
            print("Attempting to wake PJ2.")
            await asyncio.wait_for(PJ2.power.turn_on(),timeout = 1.5)
            await asyncio.sleep(5)
            print("Errors from PJ2: ", await PJ2.errors.query())
        except asyncio.TimeoutError:
            print("PJ2 timed out, Check the configuration file?")

async def PJ3Power():
        try:
            print("______________________________________")
            print("Attempting to wake PJ3.")
            await asyncio.wait_for(PJ3.power.turn_on(),timeout = 1.5)
            await asyncio.sleep(5)
            print("Errors from PJ3: ", await PJ3.errors.query())
        except asyncio.TimeoutError:
            print("PJ3 timed out, Check the configuration file?")

async def PJ4Power():
        try:
            print("______________________________________")
            print("Attempting to wake PJ4.")
            await asyncio.wait_for(PJ4.power.turn_on(),timeout = 1.5)
            await asyncio.sleep(5)
            print("Errors from PJ4: ", await PJ4.errors.query())
        except asyncio.TimeoutError:
            print("PJ4 timed out, Check the configuration file?")


async def main():
        await PJ1Power()
        await PJ2Power()
        await PJ3Power()
        await PJ4Power()


asyncio.run(main())
