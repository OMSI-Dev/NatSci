using Godot;
using System;
using System.Collections.Generic;

public partial class QRGenerator : Node2D
{
	// added two textures for two QR codes 2026-08-25 by autumn
	private TextureRect qrTextureNational;
	private TextureRect qrTextureLocal;
	private Node qrHelper;
	// added two http requests for two QR codes 2026-08-25 by autumn
	private HttpRequest LocalHTTPRequest;
	private HttpRequest NationalHTTPRequest;
	
	private List<string> nationalUrls = new List<string>();
	private List<string> localUrls = new List<string>();
	private int currentIndex = 0;
	
	private const string nationalOrgs = "https://docs.google.com/spreadsheets/d/1FrKFvzm02qJgdBJrcD_JOeaR5KWCMJ2zyb5PUP1pHw4/gviz/tq?tqx=out:csv&gid=1578975206&tq=select%20H";
	private const string localOrgs =  "https://docs.google.com/spreadsheets/d/1FrKFvzm02qJgdBJrcD_JOeaR5KWCMJ2zyb5PUP1pHw4/gviz/tq?tqx=out:csv&gid=1578975206&tq=select%20K";
	
	public override void _Ready() {
		// set references to nodes

		// added two textures for two QR codes 2026-08-25 by autumn
		qrTextureNational = GetNode<TextureRect>("QRTextureNational");
		qrTextureLocal = GetNode<TextureRect>("QRTextureLocal");

		qrHelper = GetNode("QRCodeHelper");
		LocalHTTPRequest = GetNode<HttpRequest>("LocalCSVDownloader");
		NationalHTTPRequest = GetNode<HttpRequest>("NationalCSVDownloader");
		
		GD.Print("Fetching latest version of CSV from Google Spreadsheet...");
		
		var err0 = NationalHTTPRequest.Request(nationalOrgs);
		if(err0 != Error.Ok) {
			GD.PrintErr("Failed to start HTTP request:", err0);
		}

		//changed from nationalOrgs to localOrgs 2026-08-25 by autumn
		var err1 = LocalHTTPRequest.Request(localOrgs);
		if(err1 != Error.Ok) {
			GD.PrintErr("Failed to start HTTP request:", err1);
		}
		
		LocalHTTPRequest.RequestCompleted += OnRequestCompletedLocal;
		NationalHTTPRequest.RequestCompleted += OnRequestCompletedNational;
		
		// QR codes will be updated after HTTP requests complete
	}

	//created two different HTTP request completion handlers for local and national CSVs 2026-08-25 by autumn
	
	private void OnRequestCompletedLocal(long result, long responseCode, string[] headers, byte[] body) {
		GD.Print($"Local HTTP Response Code: {responseCode}");

		// Handle redirect (307)
		if (responseCode == 307 || responseCode == 302 || responseCode == 301)
		{
			string redirectUrl = null;

			foreach (string header in headers)
			{
				if (header.StartsWith("Location:", StringComparison.OrdinalIgnoreCase))
				{
					redirectUrl = header.Substring("Location:".Length).Trim();
					break;
				}
			}

			if (!string.IsNullOrEmpty(redirectUrl))
			{
				GD.Print("Redirecting Local request to: " + redirectUrl);
				LocalHTTPRequest.Request(redirectUrl);
				return;
			} else {
				GD.PrintErr("Redirect received, but no Location header found.");
				return;
			}
		}

		// Normal response
		if (responseCode == 200)
		{
			string csvContent = System.Text.Encoding.UTF8.GetString(body);
			GD.Print("Local CSV data received:\n" + csvContent);
		
			ParseCsvLocal(csvContent);
		
			if(localUrls.Count > 0) {
				currentIndex = 0;
				UpdateQRCode();
			} else {
				GD.PrintErr("No valid Local URLs parsed from CSV.");
			}
		} else {
			GD.PrintErr($"Local HTTP Error: {responseCode}");
		}
	}


	private void OnRequestCompletedNational(long result, long responseCode, string[] headers, byte[] body) {
		GD.Print($"National HTTP Response Code: {responseCode}");

		// Handle redirect (307)
		if (responseCode == 307 || responseCode == 302 || responseCode == 301)
		{
			string redirectUrl = null;

			foreach (string header in headers)
			{
				if (header.StartsWith("Location:", StringComparison.OrdinalIgnoreCase))
				{
					redirectUrl = header.Substring("Location:".Length).Trim();
					break;
				}
			}

			if (!string.IsNullOrEmpty(redirectUrl))
			{
				GD.Print("Redirecting National request to: " + redirectUrl);
				NationalHTTPRequest.Request(redirectUrl);
				return;
			} else {
				GD.PrintErr("Redirect received, but no Location header found.");
				return;
			}
		}

		// Normal response
		if (responseCode == 200)
		{
			string csvContent = System.Text.Encoding.UTF8.GetString(body);
			GD.Print("National CSV data received:\n" + csvContent);
		
			ParseCsvNational(csvContent);
		
			if(nationalUrls.Count > 0) {
				currentIndex = 0;
				UpdateQRCode();
			} else {
				GD.PrintErr("No valid National URLs parsed from CSV.");
			}
		} else {
			GD.PrintErr($"National HTTP Error: {responseCode}");
		}
	}
	
	private void ParseCsvLocal(string csv) {
		localUrls.Clear();
		
		string[] lines = csv.Split('\n');
		
		GD.Print($"DEBUG: Total CSV lines: {lines.Length}");
		if (lines.Length > 0) GD.Print($"DEBUG: First line: '{lines[0]}'");
		if (lines.Length > 1) GD.Print($"DEBUG: Second line: '{lines[1]}'");
		
		// Skip first line (header row) and start from index 1
		for (int i = 1; i < lines.Length; i++) {
			string trimmed = lines[i].Trim();
			// Remove surrounding quotes if present
			if (trimmed.StartsWith("\"") && trimmed.EndsWith("\"") && trimmed.Length > 1) {
				trimmed = trimmed.Substring(1, trimmed.Length - 2);
			}
			if(!string.IsNullOrEmpty(trimmed)) {
				localUrls.Add(trimmed);
			}
		}
		GD.Print("Local CSV parsed. ", localUrls.Count, " Local URLs found.");
		if (localUrls.Count > 0) GD.Print($"DEBUG: First URL in list: '{localUrls[0]}'");
	}
	
	private void ParseCsvNational(string csv) {
		nationalUrls.Clear();
		
		string[] lines = csv.Split('\n');
		
		GD.Print($"DEBUG: Total CSV lines: {lines.Length}");
		if (lines.Length > 0) GD.Print($"DEBUG: First line: '{lines[0]}'");
		if (lines.Length > 1) GD.Print($"DEBUG: Second line: '{lines[1]}'");
		
		// Skip first line (header row) and start from index 1
		for (int i = 1; i < lines.Length; i++) {
			string trimmed = lines[i].Trim();
			// Remove surrounding quotes if present
			if (trimmed.StartsWith("\"") && trimmed.EndsWith("\"") && trimmed.Length > 1) {
				trimmed = trimmed.Substring(1, trimmed.Length - 2);
			}
			if(!string.IsNullOrEmpty(trimmed)) {
				nationalUrls.Add(trimmed);
			}
		}
		GD.Print("National CSV parsed. ", nationalUrls.Count, " National URLs found.");
		if (nationalUrls.Count > 0) GD.Print($"DEBUG: First URL in list: '{nationalUrls[0]}'");
	}
		
	public override void _Input(InputEvent @event) {
		if (@event is InputEventKey keyEvent && keyEvent.Pressed && !keyEvent.Echo) {
			if(nationalUrls.Count == 0) {
				return;
			}
			
			if (keyEvent.Keycode == Key.Right) {
				currentIndex = (currentIndex + 1) % nationalUrls.Count;
				UpdateQRCode();
			} else if (keyEvent.Keycode == Key.Left) {
				currentIndex = (currentIndex - 1 + nationalUrls.Count) % nationalUrls.Count;
				UpdateQRCode();
			}
		}
	}
	
	//Update this function for two QR codes (National and Local)
	private void UpdateQRCode() {
		if(currentIndex < nationalUrls.Count && currentIndex >= 0) {
			string nationalUrl = nationalUrls[currentIndex];
			GD.Print("Updating National QR code to: ", nationalUrl);
			var resultNational = qrHelper.Call("generate_qr", nationalUrl, 8);
			
			if(resultNational.VariantType == Variant.Type.Object && resultNational.As<Image>() is Image qrImageNational && !qrImageNational.IsEmpty()) {
			GD.Print("National QR Image generated successfully!\n");

			ImageTexture textureNational = ImageTexture.CreateFromImage(qrImageNational);
			qrTextureNational.Texture = textureNational;
			} else {
				GD.PrintErr("Failed to generate National QR image.");
			}
		}

		if(currentIndex < localUrls.Count && currentIndex >= 0) {
			string localUrl = localUrls[currentIndex];
			GD.Print("Updating Local QR code to: ", localUrl);
			var resultLocal = qrHelper.Call("generate_qr", localUrl, 8);
			
			if(resultLocal.VariantType == Variant.Type.Object && resultLocal.As<Image>() is Image qrImageLocal && !qrImageLocal.IsEmpty()) {
			GD.Print("Local QR Image generated successfully!\n");

			ImageTexture textureLocal = ImageTexture.CreateFromImage(qrImageLocal);
			qrTextureLocal.Texture = textureLocal;
			} else {
				GD.PrintErr("Failed to generate Local QR image.");
			}
		}
	}
}
