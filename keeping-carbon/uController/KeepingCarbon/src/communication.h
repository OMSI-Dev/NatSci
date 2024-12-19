MoToTimer heartBeatTimer;
bool on;

void heartBeat()
{
    if(!heartBeatTimer.running())
    {
        digitalWrite(13,on);
        on = !on;
        heartBeatTimer.setTime(400);
    }
}
void connectCom()
{
    Serial.begin(115200);
    Serial.setTimeout(5);
    
    // digitalWrite(13,HIGH);

    // digitalWrite(13,LOW);
}

byte comRead()
{
    const int BUFFER_SIZE = 1; //1 equals the 1 byte of information before '\n' 
    byte buf[BUFFER_SIZE];
    Serial.readBytesUntil('\n', buf, BUFFER_SIZE);

    return buf[0];
}

void comSend(byte dataOut)
{   
    Serial.println(dataOut);
}