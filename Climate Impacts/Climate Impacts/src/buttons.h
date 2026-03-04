#include <Timer.h>

Bounce2::Button btn1 = Bounce2::Button();
Bounce2::Button btn2 = Bounce2::Button();
Bounce2::Button btn3 = Bounce2::Button();
Bounce2::Button btn4 = Bounce2::Button();
Bounce2::Button btn5 = Bounce2::Button();

#define btnInput1 2
#define btnInput2 3
#define btnInput3 4
#define btnInput4 5
#define btnInput5 6

#define btn1English 1
#define btn1Spanish 2

#define btn2English 3
#define btn2Spanish 4

#define btn3English 5
#define btn3Spanish 6

#define btn4English 7
#define btn4Spanish 8

#define btn5English 9
#define btn5Spanish 10

#define btn1Channel 0
#define btn2Channel 1
#define btn3Channel 2
#define btn4Channel 3
#define btn5Channel 4

uint8_t btn1State = 0, btn2State = 0, btn3State = 0, btn4State = 0, btn5State = 0;

MoToTimer btn1Timeout, btn2Timeout, btn3Timeout, btn4Timeout, btn5Timeout;

uint16_t timeout = 200;

void attachButtons()
{
    btn1.attach(btnInput1, INPUT_PULLUP);
    btn1.setPressedState(LOW);
    btn1.interval(5);

    btn2.attach(btnInput2, INPUT_PULLUP);
    btn2.setPressedState(LOW);
    btn2.interval(5);

    btn3.attach(btnInput3, INPUT_PULLUP);
    btn3.setPressedState(LOW);
    btn3.interval(5);

    btn4.attach(btnInput4, INPUT_PULLUP);
    btn4.setPressedState(LOW);
    btn4.interval(5);

    btn5.attach(btnInput5, INPUT_PULLUP);
    btn5.setPressedState(LOW);
    btn5.interval(5);
}

void buttonUpdate()
{
    btn1.update();
    btn2.update();
    btn3.update();
    btn4.update();
    btn5.update();
}

void buttonPress()
{
    if (btn1.isPressed() && !btn1Timeout.running())
    {
        switch (btn1State)
        {
        case 0:
            // play English
            playAudio(btn1English, btn1Channel);
            btn1State = 1;
            break;

        case 1:
            // play Spanish
            stopAudioTrack(btn1English);
            playAudio(btn1Spanish, btn1Channel);
            btn1State = 2;
            break;
        case 2:
            // Stop Audio
            stopAudioTrack(btn1Spanish);
            btn1State = 0;
            break;
        default:
            break;
        }

        btn1Timeout.setTime(timeout);
    }

    if (btn2.isPressed() && !btn2Timeout.running())
    {
        switch (btn2State)
        {
        case 0:
            // play English
            playAudio(btn2English, btn2Channel);
            btn2State = 1;
            break;

        case 1:
            // play Spanish
            stopAudioTrack(btn2English);
            playAudio(btn2Spanish, btn2Channel);
            btn2State = 2;
            break;
        case 2:
            // Stop Audio
            stopAudioTrack(btn2Spanish);
            btn2State = 0;
            break;
        default:
            break;
        }
        btn2Timeout.setTime(timeout);
    }

    if (btn3.isPressed() && !btn3Timeout.running())
    {
        switch (btn3State)
        {
        case 0:
            // play English
            playAudio(btn3English, btn3Channel);
            btn3State = 1;
            break;

        case 1:
            // play Spanish
            stopAudioTrack(btn3English);
            playAudio(btn3Spanish, btn3Channel);
            btn3State = 2;
            break;
        case 2:
            // Stop Audio
            stopAudioTrack(btn3Spanish);
            btn3State = 0;
            break;
        default:
            break;
        }
        btn3Timeout.setTime(timeout);
    }

    if (btn4.isPressed() && !btn4Timeout.running())
    {
        switch (btn4State)
        {
        case 0:
            // play English
            playAudio(btn4English, btn4Channel);
            btn4State = 1;
            break;

        case 1:
            // play Spanish
            stopAudioTrack(btn4English);
            playAudio(btn4Spanish, btn4Channel);
            btn4State = 2;
            break;
        case 2:
            // Stop Audio
            stopAudioTrack(btn4Spanish);
            btn4State = 0;
            break;
        default:
            break;
        }
        btn4Timeout.setTime(timeout);
    }

    if (btn5.isPressed() && !btn5Timeout.running())
    {
        switch (btn5State)
        {
        case 0:
            // play English
            playAudio(btn5English, btn5Channel);
            btn5State = 1;
            break;

        case 1:
            // play Spanish
            stopAudioTrack(btn5English);
            playAudio(btn5Spanish, btn5Channel);
            btn5State = 2;
            break;
        case 2:
            // Stop Audio
            stopAudioTrack(btn5Spanish);
            btn5State = 0;
            break;
        default:
            break;
        }
        btn5Timeout.setTime(timeout);
    }
}