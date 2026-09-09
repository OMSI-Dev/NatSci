
void printButtonStatus() 
{   
    PC.println("__________________________");
    PC.print("Start: ");
    PC.println(startBtn.isPressed());
    PC.print("Easy: ");
    PC.println(easyBtn.isPressed());
    PC.print("Medium: ");
    PC.println(medBtn.isPressed());
    PC.print("Hard: ");
    PC.println(hardBtn.isPressed());
    PC.println("__________________________"); 
}

void printResetStatus()
{
  PC.println("__________________________");
  PC.print("Game Status: ");
  PC.println(gameOn);

  PC.print("points: ");
  PC.println(points);

  PC.print("Mole Tick: ");
  PC.println(moleTicks);

  PC.print("Remove Tick: ");
  PC.println(removeTick);

  PC.print("All timer status: ");
  PC.print(moleTimer.running());
  PC.print("|");
  PC.print(moleTicker.running());
  PC.print("|");
  PC.print(gameTimer.running());
  PC.println("__________________________");

}