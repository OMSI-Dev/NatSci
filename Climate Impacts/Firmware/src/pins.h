
#define btnPWM1 7
#define btnPWM2 8
#define btnPWM3 9
#define btnPWM4 10
#define btnPWM5 11

#define btnInput1 2
#define btnInput2 3
#define btnInput3 4
#define btnInput4 5
#define btnInput5 6

void setPins()
{

    pinMode(btnPWM1, OUTPUT);
    pinMode(btnPWM2, OUTPUT);
    pinMode(btnPWM3, OUTPUT);
    pinMode(btnPWM4, OUTPUT);
    pinMode(btnPWM5, OUTPUT);

    pinMode(btnInput1, INPUT_PULLUP);
    pinMode(btnInput2, INPUT_PULLUP);
    pinMode(btnInput3, INPUT_PULLUP);
    pinMode(btnInput4, INPUT_PULLUP);
    pinMode(btnInput5, INPUT_PULLUP);
}