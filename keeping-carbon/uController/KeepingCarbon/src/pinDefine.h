/* Pinout 
   BtnPixels 3-7
   Btn 23-16
*/

//create objects
Haxx<1> btn1Light, btn2Light, btn3Light, btn4Light, btn5Light;
CRGB pointLight[10];

MoToTimer gameTimer, moleTimer,moleTicker,removeMole;

Bounce2::Button startBtn = Bounce2::Button();
Bounce2::Button easyBtn = Bounce2::Button();
Bounce2::Button medBtn = Bounce2::Button();
Bounce2::Button hardBtn = Bounce2::Button();
// Bounce2::Button Btn1 = Bounce2::Button();
// Bounce2::Button Btn2 = Bounce2::Button();
// Bounce2::Button Btn3 = Bounce2::Button();
Bounce2::Button Btn4 = Bounce2::Button();
Bounce2::Button Btn5 = Bounce2::Button();
Bounce2::Button Btn6 = Bounce2::Button();
Bounce2::Button Btn7 = Bounce2::Button();

//create timing vars
uint16_t moleTicks = 700, removeTick = 650;
uint8_t points, lastMole;
uint32_t lastUpdate;
//game vars
bool gameOn;

//decalre functions
void reset();
void printButtonStatus();

//light vars
uint8_t b = 255;

//Serial Names
#define section1 Serial1 
#define section2 Serial2 
#define section3 Serial3 
