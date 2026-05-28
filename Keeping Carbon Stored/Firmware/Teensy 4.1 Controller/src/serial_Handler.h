const uint8_t BUTTONDATABUFFER = 2;
uint8_t data1[BUTTONDATABUFFER], data2[BUTTONDATABUFFER], data3[BUTTONDATABUFFER], data4[BUTTONDATABUFFER];
uint8_t data5[BUTTONDATABUFFER], data6[BUTTONDATABUFFER], data7[BUTTONDATABUFFER];
/*
The following pins need to have an inverted RTS Pin using the modified framework.
 XBAR Pins 1, 2, 3, 4, 5, 7, 8, 30, 31, 32, 33

*/
#define Serial1RTS 6
#define Serial2RTS 9
#define Serial3RTS 10
#define Serial4RTS 11
#define Serial5RTS 12

/*
This is wrong on the current circuit board 5/26 (V1.3)
Version 1.4 has it corrected but needs to be sent out yet.
Serial6RTS is connected to a 3.3V pin. D:
The correct pins are:
#define Serial6RTS 26
#define Serial7RTS 27
*/

#define Serial7RTS 26

#define Serial1CTS 2
#define Serial2CTS 3
#define Serial3CTS 4
#define Serial4CTS 5
#define Serial5CTS 30
#define Serial6CTS 31
#define Serial7CTS 32

void clearBuffer(uint8_t dataArray[]);
#define debug

void setSerial1()
{
    Serial1.begin(115200, SERIAL_8E1);
    Serial1.attachRts(Serial1RTS);
    Serial1.attachCts(Serial1CTS);
    while (!Serial1)
    {
#ifdef debug
        Serial.println("Waiting for Serial1 two begin...");
#endif
    }

#ifdef debug
    Serial.println("Serial 1 has started.");
#endif
clearBuffer(data1);
}

void setSerial2()
{
    Serial2.begin(115200, SERIAL_8E1);
    Serial2.attachRts(Serial2RTS);
    Serial2.attachCts(Serial2CTS);
    while (!Serial2)
    {
#ifdef debug
        Serial.println("Waiting for Serial 2 two begin...");
#endif
    }

#ifdef debug
    Serial.println("Serial 2 has started.");
#endif
clearBuffer(data2);
}

void setSerial3()
{
    Serial3.begin(115200, SERIAL_8E1);
    Serial3.attachRts(Serial3RTS);
    Serial3.attachCts(Serial3CTS);
    while (!Serial3)
    {
#ifdef debug
        Serial.println("Waiting for Serial3 two begin...");
#endif
    }

#ifdef debug
    Serial.println("Serial 3 has started.");
#endif
clearBuffer(data3);
}

void setSerial4()
{
    Serial4.begin(115200, SERIAL_8E1);
    Serial4.attachRts(Serial4RTS);
    Serial4.attachCts(Serial4CTS);
    while (!Serial4)
    {
#ifdef debug
        Serial.println("Waiting for Serial4 two begin...");
#endif
    }

#ifdef debug
    Serial.println("Serial 4 has started.");
#endif
clearBuffer(data4);
}

void setSerial5()
{
    Serial5.begin(115200, SERIAL_8E1);
    Serial5.attachRts(Serial5RTS);
    Serial5.attachCts(Serial5CTS);
    while (!Serial5)
    {
#ifdef debug
        Serial.println("Waiting for Serial5 two begin...");
#endif
    }

#ifdef debug
    Serial.println("Serial 5 has started.");
#endif
clearBuffer(data5);
}

void setSerial6()
{
    Serial6.begin(115200, SERIAL_8E1);
    // Serial6.attachRts(Serial6RTS);
    // Serial6.attachCts(Serial6CTS);
    while (!Serial6)
    {
#ifdef debug
        Serial.println("Waiting for Serial6 two begin...");
#endif
    }

#ifdef debug
    Serial.println("Serial 6 has started.");
#endif
clearBuffer(data6);
}

void setSerial7()
{
    Serial7.begin(115200, SERIAL_8E1);
    Serial7.attachRts(Serial7RTS);
    Serial7.attachCts(Serial7CTS);
    while (!Serial7)
    {
#ifdef debug
        Serial.println("Waiting for Serial7 two begin...");
#endif
    }

#ifdef debug
    Serial.println("Serial 7 has started.");
#endif
clearBuffer(data7);
}




// READ FROM ROW A
void readSerial1()
{
    if (Serial1.available())
    {
        // load buffer
        Serial1.readBytesUntil('\0', data1, BUTTONDATABUFFER);

        // This sends to Godot.
        Serial.print("A");
        Serial.println(data1[0]);
        clearBuffer(data1);
    }
}

void readSerial2()
{
    if (Serial2.available())
    {
        // load buffer
        Serial2.readBytesUntil('\n', data2, BUTTONDATABUFFER);


        // This sends to Godot.
        Serial.print("B");
        Serial.println(data2[0]);
        clearBuffer(data2);
    }
}

void readSerial3()
{
    if (Serial3.available())
    {
        // load buffer
        Serial3.readBytesUntil('\n', data3, BUTTONDATABUFFER);

        // This sends to Godot.
        Serial.print("C");
        Serial.println(data3[0]);
        clearBuffer(data3);
    }
}

void readSerial4()
{
    if (Serial4.available())
    {
        // load buffer
        Serial4.readBytesUntil('\n', data4, BUTTONDATABUFFER);

        // This sends to Godot.
        Serial.print("D");
        Serial.println(data4[0]);
        clearBuffer(data4);
    }
}

void readSerial5()
{
    if (Serial5.available())
    {
        // load buffer
        Serial5.readBytesUntil('\n', data5, BUTTONDATABUFFER);

        // This sends to Godot.
        Serial.print("E");
        Serial.println(data5[0]);
        clearBuffer(data5);
    }
}

void readSerial6()
{
    if (Serial6.available())
    {
        // load buffer
        Serial6.readBytesUntil('\n', data6, BUTTONDATABUFFER);

        // This sends to Godot.
        Serial.print("F");
        Serial.println(data6[0]);
        clearBuffer(data6);
    }
}

void readSerial7()
{
    if (Serial7.available())
    {
        // load buffer
        Serial7.readBytesUntil('\n', data7, BUTTONDATABUFFER);

        // This sends to Godot.
        Serial.print("G");
        Serial.println(data7[0]);
        clearBuffer(data7);
    }
}

void clearBuffer(uint8_t dataArray[])
{
    for (int i = 0; i < BUTTONDATABUFFER; i++)
    {
        dataArray[i] = 0;
    }
}