/*
* This script should be autoloaded into the scene.
* It needs to be used by everything throughout the game.
* Set this in Project Settings, Global tab and add this script
* to the global path. Then it can be called as a vairable just
* like any object.
*
* Keeping Carbon Stored - SERIAL COMMUNICATION
* Nat Sci Hall - OMSI
* Calico Rose
* This script allows serial data to be sent and recieved.
*/

using Godot;
using System;
using System.IO.Ports;
using System.Threading.Tasks;
using System.Linq;

public partial class SerialCom : Node2D
{
	SerialPort serialPort;
	string data;
	bool received      = false;
	bool delayFinished = false;
	string[] dataSplit;

	public override void _Ready()
	{
		string portName  = "";
		string[] comList = System.IO.Ports.SerialPort.GetPortNames();

		// print out connected ports (for testing)
		/* for(int n = 0; n < comList.Length; n++) {
			GD.Print(comList[n]);
		} */

		// pick port based on amount of connected devices, assume it is last in line
		if (comList.Length == 0) {
			GD.PrintErr("[SerialCom] No COM ports found. Is the device plugged in?");
			return;
		}

		// Pick the last port in the list
		portName = comList[comList.Length - 1];

		GD.Print("Port selected: " + portName);

		// Set port properties.
		serialPort      = new SerialPort {
			PortName    = portName,
			BaudRate    = 9600,
			ReadTimeout = 5,
			DiscardNull = true
		};

		// Try to open serial.
		try { serialPort.Open(); }
		catch(System.Exception) {
			serialPort.Close();
			throw;
		}
		finally {
			if(serialPort.IsOpen) { GD.Print("Connected to port.");
			} else { GD.Print("Could not connect to port."); }

			GD.Print("Setup finished.");
		}

		// Once this is called, it exists the function
		// So any prints must happen before it
		//serialPort.Open();
	}

	public override void _Process(double delta)
	{
		if(serialPort == null || !serialPort.IsOpen) {
			//GD.Print("Serial port not open.");
			return;
		}

		// Try to read, ignore timeout errors to prevent a flood of debug errors
		try {
			// ReadLine() will hold the data in the variable
			// until it is changed. Problems with being able to
			// equate the string values using readline
			// ReadExisting() will hold the data in the variable
			// only for the moment that it is recieved
			data = serialPort.ReadExisting();
		}
		catch(System.Exception) {
			// Here to ignore timeout errors.
		}

		// If there's no data sent, just return.
		// Prevents NullReferenceException Error to try and
		// reference data when there is no data incoming.
		if(data == null) {
			return;
		} else {
			//dataSplit = data.Split(':');
			dataSplit   = data.Select(c => c.ToString()).ToArray();
		}
	}

	public void sendData(string data) {
		// By default, NewLine is "\r\n". Set to "\n".
		serialPort.NewLine = "\n";
		serialPort.WriteLine(data);
	}

	public string getRawData() {
		return data;
	}

	public string[] getSplit() {
		return dataSplit;
	}

	private async void DelayCall(float sec) {
		GD.Print("Delay starting...");
		await ToSignal(GetTree().CreateTimer(sec), SceneTreeTimer.SignalName.Timeout);
		GD.Print("Delay finished.");
		if(!delayFinished) { delayFinished = true; }
	}
}
