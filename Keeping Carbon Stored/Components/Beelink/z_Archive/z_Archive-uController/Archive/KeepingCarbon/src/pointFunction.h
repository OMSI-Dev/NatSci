

//set to the outside of the array, to allow the first gamble to pick any of the buttons
uint8_t lastSection1Gamble=7,lastSection2Gamble=7,lastSection3Gamble=7;
//temp holder for gambled button
uint8_t section1Gamble,section2Gamble,section3Gamble;

void game()
{
  //sendMoles, randomly picks a button and adds it to the section array
  sendMoles();
  //checks if they got a point or a miss
  checkSections();
  

}

void sendMoles()
{
  //Generate moles for every section regardless of diffuculty
  //only send multiple sections if need, 
  //each section can be activated at any difficulty!
  //Easy = one button from one section at a time
  //Medium = one button from two sections at a time
  //Hard = one button from three sections at a time

  //generate first random button to turn on.
  section1Gamble = random8(0,5);
  section2Gamble = random8(0,5);
  section3Gamble = random8(0,5);

  checkForReroll();

  //update the sections array
  createButtonArray(section1Gamble,1);
  createButtonArray(section2Gamble,2);
  createButtonArray(section3Gamble,3);

  //update last gamble to prevent the same light from turning on
  lastSection1Gamble = section1Gamble;
  lastSection2Gamble = section2Gamble;
  lastSection2Gamble = section3Gamble;

}

void checkForReroll()
{
  if (section1Gamble == lastSection1Gamble)
  {
    section1Gamble = random8(0,5);
    lastSection1Gamble = section1Gamble;
  }

  if (section2Gamble == lastSection2Gamble)
  {
    section2Gamble = random8(0,5);
    lastSection2Gamble = section2Gamble;
  }

  if (section3Gamble == lastSection3Gamble)
  {
    section3Gamble = random8(0,5);
    lastSection3Gamble = section3Gamble;
  }


}

void createButtonArray(uint8_t btnPos,uint8_t arrayNum)
{
  
  //update the arrays
  //btn1-6 1 = turn on light
  //array[0,0,0,0,0,0]
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