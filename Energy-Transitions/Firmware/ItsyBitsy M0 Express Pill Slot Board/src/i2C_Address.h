/*
Aaron De Lanty
4/16/2026
I2C addressing based on GPIO input.
This header should run before Wire is started.

*/

#define aPin 3
#define bPin 4
#define cPin 12
#define dPin 7

 bool A=false,B=false,C=false,D=false;

 //Start with assuming the address is always 0x08
 u_int16_t addr = 0x08;
 u_int16_t addrPin = 0;
 //This array holds the pincount total based on the truth table. 
 // 10 unique addresses for 10 boards
 uint16_t addrList[10] = {0, 1, 3, 5, 9, 4, 6, 10, 8, 12};
 /*
 This array holds the actual addresses
 0x00-0x07 are reserved by the I2C protocol
 New mapping with 10 unique addresses, 4 type categories:
   0x08 (none)   = Buoy   (accepts Buoy + Wind)
   0x09 (A)      = Dam    (accepts Dam + Wind + Solar)
   0x0A (B)      = Geo    (accepts Geo + Wind + Solar)
   0x0B (C)      = Solar  (accepts Solar + Wind)
   0x0C (D)      = Buoy   (accepts Buoy + Wind)
   0x0D (AB)     = Dam    (accepts Dam + Wind + Solar)
   0x0E (AC)     = Geo    (accepts Geo + Wind + Solar)
   0x0F (AD)     = Solar  (accepts Solar + Wind)
   0x10 (BC)     = Dam    (accepts Dam + Wind + Solar)
   0x11 (BD)     = Geo    (accepts Geo + Wind + Solar)
*/
 uint16_t addrID[10] = {0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11};

 void setPins ()
 {
    Serial.println("Address pins set.");
    pinMode(aPin,INPUT_PULLUP);
    pinMode(bPin,INPUT_PULLUP);
    pinMode(cPin,INPUT_PULLUP);
    pinMode(dPin,INPUT_PULLUP);
 }

 void findAddr()
 {
    for(uint8_t i = 0; i<10; i++)
    {
        if(addrList[i] == addrPin)
        {
         addr = addrID[i]; 
        }
    }
    addrPin = 0;
 }

 void readPins ()
 {
    Serial.println("Reading address pins.");
    A = !digitalRead(aPin);
    B = !digitalRead(bPin);
    C = !digitalRead(cPin);
    D = !digitalRead(dPin);

    //Just for debug.
    Serial.print("A: ");
    Serial.print(A);
    Serial.print("|B: ");
    Serial.print(B);
    Serial.print("|C: ");
    Serial.print(C);
    Serial.print("|D: ");
    Serial.println(D);

    //Assign odd values to prevent overlapping.
    if(A){addrPin += 1;}
    if(B){addrPin += 3;}
    if(C){addrPin += 5;}
    if(D){addrPin += 9;}

    //Pin total is sorted through the array.
    Serial.print("Pin Total: ");
    Serial.println(addrPin);
 }

uint8_t setAddr()
{
    readPins();
    findAddr();

    return addr;
}