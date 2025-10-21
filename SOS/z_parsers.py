import string
DELIMITER = ";"


def parseConfig(ConfigFile,debug = False):
    """
    parseConfig(ConfigFile,debug = False)
    This function parses the database data in SlideFile to be used.
    Input: ConfigFile is a string of the full path to the file to be parsed.	
            all text after "#" is ignored on a line
            keywords are sos_ip, port, slideshow, database
            values follow a keyword and an equals sign
            slidewhow, database are complete paths
    Output: (success,config_dict)
            success - True/False for success of parse
            config_dict - a dictionary of the keys being the options in the
            config and the values being the option values
            options:
                sos_ip
                port
                slideshow
                database
                slide_timer
    """
    config_dict = {'sos_ip':None,
                   'port':None,
                   'default_path':None,
                   'default_name':None,
                   'slide_timer':None}
    required_options = ['sos_ip','port','default_path',
                        'default_name','slide_timer']
    integer_options = ['port']
    try:
        f = open(ConfigFile,'r')
    except:
        print( "Config File:")
        print (ConfigFile)
        print ("File does not exist")
        return (False,None)
    lnum = 0
    for line in f:
        lnum += 1
        if line.find("="):
            split = str.split(line,'#',1)
            if split[0].find("="):
                split = str.split(split[0],'=',1)
                if len(split)==2:
                    cmd = split[0].strip()
                    value = split[1].strip()
                    if cmd in config_dict.keys():
                        if cmd in integer_options:
                            if value.isdigit():
                                config_dict[cmd] = int(value)
                        else:    
                            config_dict[cmd] = value

    f.close()        
    if debug:
        for i in config_dict.keys():
            print (str(i) + " = "+ str(config_dict[i]))
    missing = []
    for i in required_options:
        if config_dict[i] == None:
            print ("Config File Missing Required element: " + str(i))
            missing.append(i)
    if len(missing)!=0:
        return (False, None)
    else:
        return (True,config_dict)



def parseSlideNames(SlideFile,debug = False):
    """ 
    parseSlideNames(SlideFile,debug = False)
    This function parses the database data in SlideFile to be used.
    Input: SlideFile is a string of the full path to the file to be parsed
           The file is to be a comma seperated file with the slide number on
           left column followed by a "," and the clip name
    
    Output: (success,dictionry)
           success - True/False for success
           dictionary - a python dictionary with keys being the first
           column of the file and the value being the second column in the file.
    ***if file doesn't exist, or error, returns imcomplete dictionary
    """
    dictionary = {}
    
    try:
        f = open(SlideFile,'r')
    except:
        print ("Database File:" + str(SlideFile) + "Could not be opened")
        return (False,dictionary)
    lnum = 0
    for line in f:
        lnum += 1
        line = str.split(line,'#',1)
        splits = str.split(line[0],DELIMITER,1)
        if len(splits)>1:
            numbers = str.split(splits[1].strip(),DELIMITER)
            dc_numbers = []
            for i in numbers:
                success = True
                i = i.strip()
                if i.isdigit():
                    dc_numbers.append(int(i))
                else:
                    print ("Ignoring invalid line: " + str(lnum))
                    success = False
            if success:
                name = splits[0].strip()
                if debug:
                    print ("adding "+str(name)+" to slide #"+ str(dc_numbers))
                if name != '':
                    dictionary[name] = dc_numbers

    f.close()
    return (True,dictionary)


def add_name_file(SFile,totalslides,name):
    Success = False
    try:
        f = open(SFile,'a')
        f.write(name+' '+DELIMITER+' '+str(totalslides)+'\n')
        Success = True
    except:
        print ("Open Write Fail")
    if 1:
        f.close()
    #except:
    #    pass
    return Success

nameDict = {}

# def main():
#     slides = "C:/Users/Landtree/Documents/GitHub/SOS_Now-Playing/Archive/SOS/v1.1/noaa_042013.txt"
#     nameDict = parseSlideNames(slides)    
#     #print(nameDict)
    
# main()