#include <Bounce2.h>
#include <Timer.h>


// Button Configuration
#define BUTTON1_PIN 2
#define BUTTON2_PIN 3
#define BUTTON3_PIN 4
#define BUTTON4_PIN 5
#define BUTTON5_PIN 6

Bounce2::Button button1 = Bounce2::Button();
Bounce2::Button button2 = Bounce2::Button();
Bounce2::Button button3 = Bounce2::Button();
Bounce2::Button button4 = Bounce2::Button();
Bounce2::Button button5 = Bounce2::Button();

MoToTimer button1Timer, button2Timer, button3Timer, button4Timer,button5Timer,debugTimer;

uint16_t buttonLock = 450, debugTime = 300;
bool buttonStates[5] = {false,false,false,false,false};

void setPins()
{
    button1.attach(BUTTON1_PIN,INPUT_PULLUP);
    button2.attach(BUTTON2_PIN,INPUT_PULLUP);
    button3.attach(BUTTON3_PIN,INPUT_PULLUP);
    button4.attach(BUTTON4_PIN,INPUT_PULLUP);
    button5.attach(BUTTON5_PIN,INPUT_PULLUP);
    Serial.println("Buttons 1-5 attached.");

    button1.interval(2);
    button2.interval(2);
    button3.interval(2);
    button4.interval(2);
    button5.interval(2);
    Serial.println("Buttons 1-5 interval updated.");

    button1.setPressedState(LOW);
    button2.setPressedState(LOW);
    button3.setPressedState(LOW);
    button4.setPressedState(LOW);
    button5.setPressedState(LOW);
    Serial.println("Buttons 1-5 press state set to LOW.");
}

void buttonUpdate()
{

    button1.update();
    button2.update();
    button3.update();
    button4.update();
    button5.update();

    if((button1.isPressed() || button2.isPressed() || button3.isPressed() || button4.isPressed() || button5.isPressed() ) && !debugTimer.running())
    {
        Serial.print("Button State: ");
        Serial.print(button1.isPressed());
        Serial.print("|");
        Serial.print(button2.isPressed());
        Serial.print("|");
        Serial.print(button3.isPressed());
        Serial.print("|");
        Serial.print(button4.isPressed());
        Serial.print("|");
        Serial.println(button5.isPressed());
        debugTimer.setTime(debugTime);
    }

    if(button1.isPressed() && !button1Timer.running() && buttonStates[0] == true)
    {
        sendSerial(1);
        Serial.println("Sent Button press.");
        button1Timer.setTime(buttonLock);
        Serial.println("Set Lock Timer.");
        buttonStates[0] = false;
        Serial.print("Button state: ");
        Serial.println(buttonStates[0]);
        clearLED(1);
    }
    
    if(button2.isPressed() && !button2Timer.running() && buttonStates[1] == true)
    {
        sendSerial(2);
        Serial.println("Sent Button press.");
        button2Timer.setTime(buttonLock);
        Serial.println("Set Lock Timer.");
        buttonStates[1] = false;
        Serial.print("Button state: ");
        Serial.println(buttonStates[1]);
        clearLED(2);
    }   

    if(button3.isPressed() && !button3Timer.running() && buttonStates[2] == true)
    {
        sendSerial(3);
        button3Timer.setTime(buttonLock);
        buttonStates[2] = false;
        clearLED(3);
    }   

    if(button4.isPressed() && !button4Timer.running() && buttonStates[3] == true)
    {
        sendSerial(4);
        button4Timer.setTime(buttonLock);
        buttonStates[3] = false;
        clearLED(4);        
    }

    if(button5.isPressed() && !button5Timer.running() && buttonStates[4] == true)
    {
        sendSerial(5);
        button5Timer.setTime(buttonLock);
        buttonStates[4] = false;
        clearLED(5);
    }
     

}

void idleButton()
{

    button1.update();
    button2.update();
    button3.update();
    button4.update();
    button5.update();

    if(button1.isPressed() && !button1Timer.running())
    {
        sendSerial(1);
        button1Timer.setTime(buttonLock);
        idle = 0;
    }
    
    if(button2.isPressed() && !button2Timer.running())
    {
        sendSerial(2);
        button2Timer.setTime(buttonLock);
        idle = 0;
    }   

    if(button3.isPressed() && !button3Timer.running())
    {
        sendSerial(3);
        button3Timer.setTime(buttonLock);
        idle = 0;
    }   

    if(button4.isPressed() && !button4Timer.running())
    {
        sendSerial(4);
        button4Timer.setTime(buttonLock);
        idle = 0;
    }

    if(button5.isPressed() && !button5Timer.running())
    {
        sendSerial(5);
        button5Timer.setTime(buttonLock);
        idle = 0;
    }

}