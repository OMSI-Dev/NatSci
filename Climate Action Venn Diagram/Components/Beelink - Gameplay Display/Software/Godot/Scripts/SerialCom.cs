/*
* Autoloaded (Project Settings > Globals > Autoload).
* Reads the Teensy 4.0 RFID handler over USB serial at 115200 baud.
*
* Protocol (see "Firmware Structure.md"):
*   "<slot>:0x<ID>"  - tag placed on reader <slot> (1|2|3), e.g. "3:0x19".
*                      "<slot>:0x0" means the slot was emptied.
*   "L"              - language button pressed.
*
* Emits:
*   PiecePlaced(slot, hexId)  - a tag was placed on a reader
*   PieceRemoved(slot)        - a reader slot was emptied
*   LanguagePressed()         - language button pressed
*
* Reading happens on a background thread; lines are queued and
* dispatched from _Process so signals fire on the main thread.
*/

using Godot;
using System;
using System.Collections.Concurrent;
using System.IO.Ports;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;

public partial class SerialCom : Node
{
	[Signal] public delegate void PiecePlacedEventHandler(int slot, int hexId);
	[Signal] public delegate void PieceRemovedEventHandler(int slot);
	[Signal] public delegate void LanguagePressedEventHandler();
	[Signal] public delegate void ConnectionChangedEventHandler(bool connected);

	// Leave empty to auto-detect. Set to e.g. "/dev/ttyACM0" to force a port.
	[Export] public string PortOverride { get; set; } = "";

	private const int BaudRate = 115200;
	private const double ReconnectIntervalSec = 2.0;

	private static readonly Regex LineFormat =
		new Regex(@"^([1-3]):0x([0-9A-Fa-f]{1,4})$", RegexOptions.Compiled);

	private SerialPort serialPort;
	private Thread readThread;
	private volatile bool runReadThread;
	private readonly ConcurrentQueue<string> lineQueue = new();

	private bool connected = false;
	private double reconnectTimer = 0;

	public bool PortConnected => connected;

	public override void _Ready()
	{
		TryConnect();
	}

	public override void _Process(double delta)
	{
		// The read thread flags a dead connection by clearing runReadThread.
		if (connected && !runReadThread) {
			Disconnect();
		}

		if (!connected) {
			reconnectTimer -= delta;
			if (reconnectTimer <= 0) {
				reconnectTimer = ReconnectIntervalSec;
				TryConnect();
			}
		}

		while (lineQueue.TryDequeue(out string line)) {
			ParseLine(line);
		}
	}

	public override void _ExitTree()
	{
		Disconnect();
	}

	private void ParseLine(string line)
	{
		line = line.Trim();
		if (line.Length == 0) {
			return;
		}

		if (line == "L") {
			GD.Print("[SerialCom] Language button pressed.");
			EmitSignal(SignalName.LanguagePressed);
			return;
		}

		Match m = LineFormat.Match(line);
		if (!m.Success) {
			GD.Print($"[SerialCom] Ignoring unrecognized line: '{line}'");
			return;
		}

		int slot = int.Parse(m.Groups[1].Value);
		int hexId = Convert.ToInt32(m.Groups[2].Value, 16);

		if (hexId == 0) {
			GD.Print($"[SerialCom] Slot {slot} emptied.");
			EmitSignal(SignalName.PieceRemoved, slot);
		} else {
			GD.Print($"[SerialCom] Slot {slot} placed 0x{hexId:X2}.");
			EmitSignal(SignalName.PiecePlaced, slot, hexId);
		}
	}

	private string PickPort()
	{
		if (!string.IsNullOrEmpty(PortOverride)) {
			return PortOverride;
		}

		string[] ports = SerialPort.GetPortNames();
		if (ports.Length == 0) {
			return null;
		}

		// The Teensy 4.0 enumerates as a USB CDC-ACM device:
		// /dev/ttyACM* on Linux, usbmodem* on macOS.
		string preferred = ports.LastOrDefault(p => p.Contains("ttyACM"))
			?? ports.LastOrDefault(p => p.Contains("usbmodem"));
		return preferred ?? ports[ports.Length - 1];
	}

	private void TryConnect()
	{
		string portName = PickPort();
		if (portName == null) {
			return;
		}

		try {
			serialPort = new SerialPort {
				PortName = portName,
				BaudRate = BaudRate,
				ReadTimeout = 500,
				NewLine = "\n",
				DiscardNull = true,
				DtrEnable = true
			};
			serialPort.Open();
			serialPort.DiscardInBuffer();
		}
		catch (Exception e) {
			GD.Print($"[SerialCom] Could not open {portName}: {e.Message}");
			serialPort?.Dispose();
			serialPort = null;
			return;
		}

		GD.Print($"[SerialCom] Connected to {portName} @ {BaudRate}.");
		connected = true;
		runReadThread = true;
		readThread = new Thread(ReadLoop) { IsBackground = true };
		readThread.Start();
		EmitSignal(SignalName.ConnectionChanged, true);
	}

	private void Disconnect()
	{
		runReadThread = false;
		try { serialPort?.Close(); } catch (Exception) { }
		readThread?.Join(1000);
		readThread = null;
		serialPort?.Dispose();
		serialPort = null;

		if (connected) {
			connected = false;
			GD.Print("[SerialCom] Disconnected. Will retry...");
			EmitSignal(SignalName.ConnectionChanged, false);
		}
	}

	private void ReadLoop()
	{
		while (runReadThread) {
			try {
				string line = serialPort.ReadLine();
				lineQueue.Enqueue(line);
			}
			catch (TimeoutException) {
				// No data this interval; keep polling.
			}
			catch (Exception) {
				// Port unplugged or closed; let the main thread reconnect.
				runReadThread = false;
			}
		}
	}

	public void SendData(string data)
	{
		if (!connected || serialPort == null) {
			GD.Print("[SerialCom] Cannot send, port not open.");
			return;
		}
		try {
			serialPort.WriteLine(data);
		}
		catch (Exception e) {
			GD.PrintErr($"[SerialCom] Write failed: {e.Message}");
		}
	}
}
