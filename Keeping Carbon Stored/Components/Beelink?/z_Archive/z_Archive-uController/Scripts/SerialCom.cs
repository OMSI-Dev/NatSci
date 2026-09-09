//install dot9, then run terminal command in dir with godot C# sln: dotnet add package System.IO.Ports --version 9.0.0
//Set to autoload(project settings -> Global) in project settings
using Godot;
using GodotPlugins.Game;
using System;
using System.IO.Ports;

public partial class SerialCom : Node
{	
	SerialPort serialPort;

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{	
		//create an empty string
		string PortName = "";
		//populate connected com ports
		string[] comList = System.IO.Ports.SerialPort.GetPortNames();
		
		

		//print out connected ports
		for(int n = 0; n<comList.Length; n++)
		{
			GD.Print(comList[n]);
		}

		//pick port based on amount of
		//connected devices, assume last in line 
		//arduino

		if(comList.Length == 1)
		{
			PortName = comList[0];
		}
		if(comList.Length == 2)
		{
			PortName = comList[1];
		}
		if(comList.Length == 3)
		{
			PortName = comList[2];
		}		

		//print out deteced port
		GD.Print("Port Detected: " + PortName);
		GD.Print("Attempting to connect");
		//Set serialPort properties
		serialPort = new SerialPort
		{
			PortName = PortName,
			BaudRate = 115200,
			ReadTimeout = 5,
			DiscardNull = true
			
		};

		//Try to open Serial
		
		try
		{
			serialPort.Open();
		}
		catch (System.Exception)
		{
			throw;	
		}


		if (serialPort.IsOpen)
		{
			GD.Print("Connected Port, ready to receive data");
		}else
		{
			GD.Print("Can't connect");
		}

	}

	public string readSerial()
	{	
		string data = null;
		//try to read, ingore timeout errors
		//to prevent a flood of debug errors
		try
		{
			data = serialPort.ReadLine();
		}
		catch (System.Exception)
		{
			//ignore timeout errors
		}
			return data;
	}

	public int readSerialByte()
	{	
		int data = 0;
		//try to read, ingore timeout errors
		//to prevent a flood of debug errors
		try
		{
			data = serialPort.ReadByte();
		}
		catch (System.Exception)
		{
			//ignore timeout errors
		}
			return data;
	}

	public void Send(string outData)
	{	
		//write data to arduino
		serialPort.WriteLine(outData);
	}
}
