#include <Bounce2.h>

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

void setPins()
{
    button1.attach(BUTTON1_PIN,INPUT_PULLUP);
    button2.attach(BUTTON2_PIN,INPUT_PULLUP);
    button3.attach(BUTTON3_PIN,INPUT_PULLUP);
    button4.attach(BUTTON4_PIN,INPUT_PULLUP);
    button5.attach(BUTTON5_PIN,INPUT_PULLUP);
    Serial.println("Buttons 1-5 attached.");

    button1.interval(5);
    button2.interval(5);
    button3.interval(5);
    button4.interval(5);
    button5.interval(5);
    Serial.println("Buttons 1-5 interval updated.");

    button1.setPressedState(LOW);
    button2.setPressedState(LOW);
    button3.setPressedState(LOW);
    button4.setPressedState(LOW);
    button5.setPressedState(LOW);
    Serial.println("Buttons 1-5 press state set to LOW.");
}

