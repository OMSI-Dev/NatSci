#include <haxx.h>

haxx jumbo,large,med;
MoToTimer flip;

#define serial Serial
#define numEffects 10
uint8_t t = 0;


void setup()
{
jumbo.attach(0,0);
large.attach(1,1);
med.attach(2,2);
Serial.begin(9600);
//while(!Serial);
serial.println("Connected");
}

void loop()
{

if(!flip.running())
{
    t++;
    if(t > numEffects){t = 0;}
    flip.setTime(5000);
}

jumbo.blue();
large.red();
med.green();

// switch (t)
// {
//     case 0:
//     light.centerRings(175,0,100,100,0);
//         break;
//     case 1:
//     light.centerSwirl(150,0,45,85,1,3);
//         break;
//     case 2:
//     light.blue();
//         break;
//     case 3:
//     light.red();
//         break;
//     case 4:
//     light.green();
//         break;
//     case 5:
//     light.centerFill(145,50,230);
//         break;
//     case 6:
//     light.ringFill(50,255,100);
//         break;
//     case 7:
//     light.chase(255,0,0,100,125,0);
//         break;
//     case 8:
//     light.chase(255,0,0,100,125,1);
//         break;
//     case 9:
//     light.chase(255,0,0,100,125,2);
//         break;
//     case 10:
//     light.loading();
//         break;
//     default:
//         // Code for any other case
//         break;
// }

}