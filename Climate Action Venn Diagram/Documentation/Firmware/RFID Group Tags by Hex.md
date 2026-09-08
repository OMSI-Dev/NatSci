Each RFID tag stores a single byte ID at page 5, byte 3 of the NTAG215 memory.



Three Categories:



\*\***Group tags: IDs 0x01 to 0x0C (1-12 in hex)**\*\*

&#x09;Stored in knownTagsGroup\[] array

&#x09;Detected by Reader 1 (Serial3)





\*\***Interest tags: IDs 0x0D to 0x18 (13-24 in hex**\*\*

&#x09;Stored in knownTagsInterest\[] array

&#x09;Detected by Reader 2 (Serial4)





\*\***Topic tags: IDs 0x19 to 0x24 (25-36 in hex)**\*\*

&#x09;Stored in knownTagsTopic\[] array

&#x09;Detected by Reader 3 (Serial5)





* When a tag is read, byte 3 from page 5 is extracted
* The code checks which array contains that byte value
* If found in the corresponding reader's array, it's a 'known tag'
* The tag ID and category number are sent via sendTag( 0







