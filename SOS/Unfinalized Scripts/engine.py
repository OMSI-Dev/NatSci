from win32com.client import constants, Dispatch
import string
import socket
import time
import sys
import getopt
import threading
from parsers import parseSlideNames, add_name_file

#Hardcoding this as it should not need to change
nowPort = 65432

class sosppEngine:
    # def __init__(self,ip,port,pp,pp_dictionary,database,mode,config,verbose):   old engine call, remove all old references     

    def __init__(self,ip,port,pp,pp_dictionary):        
        self.runme = True
        self.ip = ip
        self.port = port
        self.pp = pp
        self.pp_dictionary = pp_dictionary

    # def __init_socket__(self,ipadd,ports,attempts=None,debug=False):
    #     """
    #     init_socket(ipadd,ports,attempts=None,debug=False):
    #     Attempts to connect to ipadd and port until accept or tries exceeds attempts
    #     on connection, sends enable and returns
    #     Input:  ip address as a string
    #             port as a integer,
    #             attempts is an integer number for number of attempts before quitting
    #             bool for debug prints
    #     Output: a tuble with (success,socket)
    #             on failure, success==false and socket == None
        
    #     """
    #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     i = 0
    #     s.settimeout(4)

    #     while self.runme:
    #         try:
    #             s.connect((ipadd,ports))
    #             break
    #         except socket.error:
    #             if debug:
    #                 print ("NETWORK START FAIL")
    #             for i in range(0,5):
    #                 if not self.runme:
    #                     return (False,None)
    #                 time.sleep(0.5)
    #         i += 1
    #         if attempts:
    #             if attempts < i:
    #                 return (False,None)
    #     print ("Send Enable")
    #     s.send('enable\n') #previously commented out
    #     try:
    #         r = s.recv(1024)
    #     except:
    #         print ("Socket Error")
    #         return (False,None)
    #     if r.strip() != "R":
    #         print ("Socket Error")
    #         return (False,None)
    #     if debug:
    #         print ("Connected to ",str(ipadd),":",str(ports))
    #     return (True,s)
    
    def __init_nowSocket__(self,attempts=None,debug=False):
        """
        Connect to nowPlaying socket only. 
        """
        nowSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        nowSocket.settimeout(4)

        while self.runme:
            try:
                nowSocket.connect(("localhost", nowPort)) #connect to nowPlaying socket 
                break
            except socket.error:
                if debug:
                    print ("NETWORK START FAIL")
                for i in range(0,5):
                    if not self.runme:
                        return (False,None)
                    time.sleep(0.5)
            i += 1
            if attempts:
                if attempts < i:
                    return (False,None)
                
        return (True,nowSocket)

    # def socket_readname(self,soc,newSoc,debug=False):
    #     """
    #     **** this can likely be removed, readname function can be applied elsewhere ****
    #     socket_readname(soc,debug=False)
    #     Input: soc - an instance of a socket connected to SOS
    #     Output: (success,name)
    #             success - True/False of success
    #             name - string of the current playing slips name
    #     """
    #     line = ''
    #     try:
    #         soc.send(b"get_clip_number\n")
    #         try:
    #             line = soc.recv(1024).decode("utf-8","ignore")
    #         except:
    #             print ("Socket Error")
    #             return (False,'')
    #         num = line.strip()
    #         if not (num.isdigit()):
    #             return (True,'')
    #         if debug:
    #             print ("Number: ",str(num))
            
    #         soc.send(b"get_clip_info "+num+"\n")
    #         line = soc.recv(1024).decode("utf-8","ignore")
    #         name = line.strip()
    #         newSoc.sendall(name.encode("utf-8"))
    #     except:
    #         if debug:
    #             print ("Connection Read Fail")
    #         return (False,None)
        
    #     return (True,name)

    # def total_slides(self):
    #     total = 0
    #     for i in self.pp_dictionary.values():
    #         total = total + len(i)
    #     return total

    def run(self):
        """
        main loop of engine
        opens powerpoint and connects to SOS, maps names to slide numbers, creates slides
        """
        total_slides = self.total_slides()
        print( "Connecting to SOS . . . ",)
        success, soc = self.__init_socket__(self.ip,self.port,None,self.verbose)
        newsuccess, newSoc = self.__init_nowSocket__(None,self.verbose)

        if success:
            print ("Done")
        else:
            print ("Failed, Exiting!")
            return
        #Start Slide Show
        if self.mode:
            self.pp.launchpp(RunShow=False)
        else:
            self.pp.launchpp(RunShow=True)
        if self.verbose:
            print ("Slide Show Opened")

        p = self.pp.get_slide_total()
        if total_slides > p:
            print ("WARNING: More slides in database than in the powerpoint")

        currentslide = -1
        slides_p_clip = 0
        index_slide = 0
        time_on_slide = 0
        #Start Main Loop
        print ("Engine Started")
        while self.runme:
            time.sleep(2)
            #Get Current Name of Clip
            success,name = self.socket_readname(soc,newSoc)
            #On Fail, Try to reconnect
            if not success:
                soc.close()
                newSoc.close()
                if not self.mode:
                    self.pp.goto(1) #display slide 1 if socket fails 
                    currentslide = 1
                # while True:
                #     success,soc = self.__init_socket__(self.ip,self.port,None,self.verbose)
                #     newsuccess, newSoc = self.__init_nowSocket__(None,self.verbose)
                #     if success:
                #         success,name = self.socket_readname(soc,newSoc)
                #         if success:
                #             break
                #         else:
                #             soc.close()
                #             newSoc.close()

            if name.strip() in self.pp_dictionary.keys(): #map current clip name to slide number(s)
                slide_nums = self.pp_dictionary[name] #makes a list of slide numbers for the current clip name
            else:
                slide_nums = [1]
                if self.verbose:
                    print( "Name Not Found in Database")

            #     """
            #     ******** Slide creation mode -- can be removed ******
            #     """
            # if self.mode and slide_nums == [1] and len(name.strip())>0: #create slide mode
            #     total_slides += 1
            #     if self.verbose:
            #         print ("Adding ",str(name)," as slide ",str(total_slides))
            #     self.pp.create_slide(name,total_slides)
            #     # success = add_name_file(self.database,total_slides,name) #this is for slide creation
            #     self.pp_dictionary[name]=total_slides

                """
                main functions of displaying powerpoint slides based on sos clip names 
                """
            # elif not self.mode: #can be removed 
                if not currentslide in slide_nums: #if current slide is not in the list of slides for the current clip name
                    if self.verbose:
                        print ("Changing to Slide:" + str(slide_nums[0]))
                    slides_p_clip = len(slide_nums) #
                    time_on_slide = 0
                    index_slide = 0
                    self.pp.goto(slide_nums[0]) #go to specified slide number 
                    currentslide = slide_nums[0]
                # elif time_on_slide >= int(self.config["slide_timer"])/2.0: #commented 10/19 to take out config reference
                    #print "Changing . . . "
                    if slides_p_clip > 1:
                        index_slide = (index_slide + 1)%slides_p_clip
                        time_on_slide=0
                        #print "Index = ",index_slide
                        #print "Changing to Slide",slide_nums[index_slide]
                        self.pp.goto(slide_nums[index_slide])
                        currentslide = slide_nums[index_slide]
                elif slides_p_clip > 1:
                    time_on_slide +=2
                    #print "Time = ",time_on_slide
        soc.close()
        self.pp.close()