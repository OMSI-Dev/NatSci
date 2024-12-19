#include <Arduino.h>
#include <Timer.h>
#include <pinDefine.h>
#include <communication.h>
#include <Bounce2.h>
#include <Pulse.h>
#include <buttonFunctions.h>




void setup() 
{

  buttonSetup();

  connectCom();


}

void loop() 
{
  heartBeat();
  buttonUpate();
 // byte incoming = comRead();
  
}

