# main.py
# Windows Only
import getopt
import sys
import threading
import time
from parsers import parseConfig, parseSlideNames
from ppAccess import PowerPointShowController
from engine import sosppEngine
from nowPlaying import begin
from nowPlaying import close as nowclose


DEFAULT_CONFIG = "C:\\Users\\agreen\\Documents\\Github\\NatSci\\SOS\config.txt"

def usage():
    """prints help"""
    s = """
Science on a Sphere PP Controller
Developed by Jim Love
usage:
    -v verbose mode, prints debug messaging
    -s slide create mode
    -n name
"""
    print(s)


class io_control(threading.Thread):
    def __init__(self,engine):
        threading.Thread.__init__(self)
        self.engine = engine

    def run(self):
        time.sleep(5)
        while True:
            y = input("\nPress Y to exit\n\r")
            if y in ["y","Y"]:
                self.engine.runme = False
                print ("Exiting . . . ")
                break

def main():
    """Initializes and Runs PowerPoint based on SOS current clip name
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hsa:p:c:n:v",
                                    ["help",
                                     "slidecreator",
                                     "address=",
                                     "port=",
                                     "config=",
                                     "name="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))# "option -a not recognized"
        usage()
        sys.exit(2)
    output = None
    verbose = True
    ip_cmd = None
    port_cmd = None
    config = None
    name = None
    mode = 0
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-a", "--address"):
            ip_cmd = a
        elif o in ("-p", "--port"):
            port_cmd = a
        elif o in ("-c", "--config"):
            config = a
        elif o in ("-s", "--slidecreator"):
            mode = 1
        elif o in ("-n", "--name"):
            name = a
        else:
            assert False, "unhandled option"
    if not config:
        config = DEFAULT_CONFIG
    print ("Initializing . . . ")
    success, config_dict = parseConfig(config,verbose)
    if success:
        if ip_cmd:
            ip = ip_cmd
        else:
            ip = config_dict["sos_ip"]
        if port_cmd:
            port = port_cmd
        else:
            port = config_dict["port"]
        if name:
            slideshow = config_dict["default_path"] + name + ".ppt"
            database = config_dict["default_path"] + name + ".csv" #.txt to .csv change here
            print ("Using:")
            print (slideshow)
            print (database)
        else:
            slideshow = config_dict["default_path"] + config_dict["default_name"] + ".ppt"
            database = config_dict["default_path"] + config_dict["default_name"] + ".csv" #same change here
    else:
        print ("Error in config file")
        sys.exit(2)
    #Parse database, exit failure
    success, pp_dictionary = parseSlideNames(database,verbose)
    if success:
        if verbose:
            print ("Database Parsed Successfully")
    else:
        print ("Slide Parse Failed")
        sys.exit(1)

    pp = PowerPointShowController(slideshow)
    nowPlaying = threading.Thread(target=begin, daemon=True)
    nowPlaying.start()


    #init Engine
    eng = sosppEngine(ip,port,pp,pp_dictionary,database,mode,config_dict,verbose)
    #Start Engine
    ioc = io_control(eng)
    ioc.start()
    print("Set Controls")
    eng.run()
    time.sleep(5)
    pp.close()
    #close now playing screen
    print ("Done")

main()
