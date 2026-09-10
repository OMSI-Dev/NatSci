# Overview
This project was in a broken state. 

The truth table serves as the primary gameplay reference (Godot > docs > Truth Table.csv) 

Gameplay is driven in Godot, the framework relying on Serial output from a Teensy 4.0 (refer to '0_Firmware Structure.md')

# Clean up 
Any HTTP requests / remote sheet management has to be discarded. Local copies will be used instead of remote access.

# The Interactive Flow & Gameplay Goals
- Recieve a Hex code via Serial. 

- Store Hex Code and update state machine to register the signaled piece (interest, topic, or group pieces)

- Update state machine if signaled piece is removed

- Read the Hex Code Key (Godot > docs > Hex Codes.csv)

- Extract information from the Hex Code Key to identify gamepiece

- Store information in a state machine (extracted values of item, subcategory, and category according to 'Hex'). The state machine holds this information for each three of the categories (Interest, Topic, Group)

- Clear stored information for a category if its' respective slot returns an empty hex

- Recognize when all three pieces are successfully registered (all categories are filled with information and not empty), trigger a results phase 

- Results phase has a transitionary animation before displaying final results screen/scene. 

- Take the stored value for each respective piece (category) and compare it to the Truth Table. Generate an outcome.

# The outcome

Reference the Truth Table, identify the  matching combination of 'Interest Item', 'Group', and 'Topic'. This Truth Table should contain all possible combinations. 

- Once identified, store the following information for displaying the final results:

    National Org name, description, spanish description, URL link
  
    Local org... Choose 1 of 3 randomly (There are 3 local orgs for each outcome in the truth table) name, description, spanish description, URL link

# Serial connection 
This is not configured and has not been tested. This needs to be reworked to read serial messages from a Teensy 4.0, with Serial baud rate of 115200.
