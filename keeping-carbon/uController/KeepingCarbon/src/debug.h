
void printButtonStatus() {
    Serial.print("button press: ");
    Serial.print("1:");
    Serial.print(Btn1.isPressed());
    Serial.print("|2:");
    Serial.print(Btn2.isPressed());
    Serial.print("|3:");
    Serial.print(Btn3.isPressed());
    Serial.print("|4:");
    Serial.print(Btn4.isPressed());
    Serial.print("|5:");
    Serial.print(Btn5.isPressed());
    Serial.print("|6:");
    Serial.print(Btn6.isPressed());
    Serial.print("|7:");
    Serial.print(Btn7.isPressed());
    Serial.print("|Start:");
    Serial.println(startBtn.isPressed());
}

void printResetStatus()
{
  Serial.println("**********************");
  Serial.print("Game Status: ");
  Serial.println(gameOn);

  Serial.print("points: ");
  Serial.println(points);

  Serial.print("Mole Tick: ");
  Serial.println(moleTicks);

  Serial.print("Remove Tick: ");
  Serial.println(removeTick);


  Serial.print("R value: ");
  Serial.println(b);

  Serial.print("All timer status: ");
  Serial.print(moleTimer.running());
  Serial.print("|");
  Serial.print(moleTicker.running());
  Serial.print("|");
  Serial.print(gameTimer.running());
  Serial.println("**********************");

}