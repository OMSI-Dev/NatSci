
std::array<byte, 11> section1Buttons,section2Buttons,section3Buttons;


void game()
{
  sendMoles();
  checkSections();

}

void sendMoles()
{
  //Generate moles for every section regardless of diffuculty
  //only send multiple sections if need, 
  //each section can be activated at any difficulty!

  uint8_t section1Gamble,section2Gamble,section3Gamble;

  //generate first random button to turn on.
  section1Gamble = random8(0,5);
  section2Gamble = random8(0,5);
  section3Gamble = random8(0,5);

  createButtonArray(section1Gamble,1);



}

void createButtonArray(uint8_t btnPos,uint8_t arrayNum)
{
  
  switch (arrayNum)
  {
  case 1:
   section1Buttons[btnPos] = 1;
    break;
    case 2:
   section2Buttons[btnPos] = 1;
    break;
      case 3:
   section3Buttons[btnPos] = 1;
    break;
  default:

    break;
  }
  
}

void checkSections()
{
    auto section2Array = readSection2();
    for(byte i:section2Array)
    {
      if(i == 1)
      {
        sendToPC(1);
      }
    }
}

void updatePointLights(int points) {
    // Turn off the appropriate light if points have decreased
    for (int i = 0; i < 10; i++) {
        if (points < (i + 1) * 2) {
            pointLight[i] = CHSV(0, 0, 0); // Turn off the light
        }
    }

    // Light up the appropriate point light based on points
    for (int i = 0; i < 10; i++) {
        if (points >= (i * 2) && points < ((i + 1) * 2)) {
            pointLight[i] = CHSV(i * 25, 255, 255); // Set the hue incrementing by 10 for each LED
        }
    }

    FastLED.show();
}

void setPoints(bool correct)
{ 
  if(correct)
  {
    points++;

    Serial.println("Point Gain!");
  }else{
  if(points != 0)
    {
      Serial.println("Point loss!");
      if(points <= 2)
      {
        points = points-1;
      }
      else
      {
        points = points-3;
      }

    }
  }
  Serial.print("B: ");
  Serial.println(b);
  updatePointLights(points);
}