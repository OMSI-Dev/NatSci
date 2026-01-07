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
    //Connect to the PC
    Serial.begin(115200);
    Serial.setTimeout(5);
    //Connect to each section & set timeout
    section1.begin(115200);
    section1.setTimeout(5);

    section2.begin(115200);
    section2.setTimeout(5);

    section3.begin(115200);
    section3.setTimeout(5);

}

std::array<byte, sectionBufferSize> readSection1()
{
    //create array to hold incoming data
    std::array<byte, sectionBufferSize> buffer;
    buffer.fill(0);
    section1.readBytesUntil('\n', buffer.data(), sectionBufferSize);

    return buffer;
}

std::array<byte, sectionBufferSize> readSection2()
{
    std::array<byte, sectionBufferSize> buffer;
    buffer.fill(0);
    section2.readBytesUntil('\n', buffer.data(), sectionBufferSize);

    return buffer;
}

byte readSection3()
{
    const int sectionBufferSize = 13; //1 equals the 1 byte of information before '\n' 
    byte buf[sectionBufferSize];
    section2.readBytesUntil('\n', buf, sectionBufferSize);

    return buf[0];
}


void sendToSection1(byte dataOut)
{   
    section1.println(dataOut);
}


/**
 * @brief Send data to the connected PC
 * @param dataOut 1 = gain point 0 = remove point 3 = start Game
 */
void sendToPC(byte dataOut)
{   
    //Send add point to the PC
    if(dataOut == 1)
    {
        PC.println("+");
    }
    //Send remove point to the PC
    if(dataOut == 0)
    {
        PC.println("-");
    }

    //Send start to PC
    if(dataOut == 2)
    {
        PC.println("S");
    }
    
}