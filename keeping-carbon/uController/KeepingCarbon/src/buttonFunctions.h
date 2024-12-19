
Bounce2::Button btn1 = Bounce2::Button();

void buttonSetup()
{   
    pinMode(13,OUTPUT);
    btn1.attach(btn1pin,INPUT_PULLDOWN);
    btn1.setPressedState(LOW);
    btn1.interval(5);

}

void buttonUpate()
{
    btn1.update();

    if(btn1.pressed())
    {   
        byte temp = 1;
        comSend(temp);
    }
}