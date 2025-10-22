import string
import csv
DELIMITER = ";"


def parseConfig(ConfigFile,debug = False):
    """
    parseConfig(ConfigFile,debug = False)
    This function parses config.txt, and isolates the database file to be used as 'SlideFile'.
    Input: ConfigFile is a string of the full path to the file to be parsed.	
            all comment text following "#" is ignored 
            keywords are sos_ip, port, slideshow, database
            values follow a keyword and an equals sign
            slideshow, database are complete paths
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


# I am working here !!!!!!!!!!!!!!!!!!!!!!!!!!!!----------------------------------------
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
    """Simple, robust parser for slide files.

    Behavior:
    - Opens file with utf-8-sig to tolerate BOM.
    - Strips inline comments beginning with '#'.
    - Auto-detects delimiter: uses ';' if present in a sample, otherwise ','.
    - Uses csv.reader to recognize collections of slides through quoted fields
    - Converts numeric tokens permissively (int(float(token))).
    Returns: (True, mapping) or (False, {}) on file error.
    """
    import csv
    mapping = {}
    try:
        with open(SlideFile, 'r', encoding='utf-8-sig', newline='') as f:
            sample = f.read()
            f.seek(0)
            delim = ';' if ';' in sample else ','
            if debug:
                print(f"Auto-detected delimiter: '{delim}'")
            for lnum, raw_line in enumerate(f, start=1):
                # remove inline comment
                line = raw_line.split('#', 1)[0].strip()
                if not line:
                    continue
                try:
                    fields = next(csv.reader([line], delimiter=delim))
                except Exception as e:
                    if debug:
                        print(f"Line {lnum}: CSV parse error: {e}")
                    continue
                if len(fields) < 2:
                    if debug:
                        print(f"Line {lnum}: not enough fields")
                    continue
                name = fields[0].strip()
                # flatten numeric tokens: support numbers across multiple CSV columns
                # and also numbers embedded together like '614, 615, 616' or '614 ; 615'
                import re
                tokens = []
                for fld in fields[1:]:
                    for part in re.split(r'[;,]', fld):
                        part = part.strip()
                        if part:
                            tokens.append(part)
                if not tokens:
                    if debug:
                        print(f"Line {lnum}: no slide numbers")
                    continue
                nums = []
                bad = False
                for tok in tokens:
                    try:
                        if tok.isdigit():
                            nums.append(int(tok))
                        else:
                            nums.append(int(float(tok)))
                    except Exception:
                        bad = True
                        if debug:
                            print(f"Line {lnum}: invalid token '{tok}'")
                        break
                if bad:
                    continue
                if name:
                    mapping[name] = nums
    except FileNotFoundError:
        if debug:
            print("Database File:" + str(SlideFile) + " Could not be opened")
        return (False, {})

    return (True, mapping)


# you can stop here for a checkpoint!!!!-----------------------
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
