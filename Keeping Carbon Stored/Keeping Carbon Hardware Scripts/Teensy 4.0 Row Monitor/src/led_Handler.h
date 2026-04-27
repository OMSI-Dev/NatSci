//Used to convert data packet to an RGB value
uint8_t red = 0;
uint8_t green = 0;
uint8_t blue = 0;

void rgbValues()
{
  ///convert to packed RGB packet
  uint32_t r1Temp = (data[1] - '0') * 100;
  uint32_t r2Temp = (data[2] - '0') *  10;
  uint32_t  r3Temp = (data[3] - '0');
  
  uint32_t g1Temp = (data[4] - '0') * 100;
  uint32_t g2Temp = (data[5] - '0') *  10;
  uint32_t g3Temp = (data[6] - '0' );

  uint32_t b1Temp = (data[7] - '0') * 100;
  uint32_t b2Temp = (data[8] - '0') * 10;
  uint32_t b3Temp = (data[9] - '0');
 
  red = (r1Temp + r2Temp + r3Temp);
  green = (g1Temp + g2Temp + g3Temp);
  blue = (b1Temp + b2Temp + b3Temp);

}

void clearRGB()
{
  red = 0;
  green = 0;
  blue = 0;
}