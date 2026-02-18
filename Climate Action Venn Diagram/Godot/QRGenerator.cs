using Godot;
using System;
using System.Collections.Generic;

public partial class QRGenerator : Node2D
{
	private TextureRect qrTexture;
	private Node qrHelper;
	private HttpRequest httpRequest;
	
	private List<string> urls = new List<string>();
	private int currentIndex = 0;
	
	private const string csvUrl = "https://docs.google.com/spreadsheets/d/1pv89RwITOwscfeXnz-TUFJJm-rpUkeqtwnS6BAnKR7Q/export?format=csv&gid=0";
	
	public override void _Ready() {
		// set references to nodes
		qrTexture = GetNode<TextureRect>("QRTexture");
		qrHelper = GetNode("QRCodeHelper");
		httpRequest = GetNode<HttpRequest>("CSVDownloader");
		
		GD.Print("Fetching latest version of CSV from Google Spreadsheet...");
		
		var err = httpRequest.Request(csvUrl);
		if(err != Error.Ok) {
			GD.PrintErr("Failed to start HTTP request:", err);
		}
		
		httpRequest.RequestCompleted += OnRequestCompleted;
		
		//LoadUrlsFromCsv("res://url_list.csv");
		
		//if(urls.Count == 0) {
			//GD.PrintErr("No URLS found in CSV file.");
			//return;
		//}
		
		UpdateQRCode();
	}
	
	private void OnRequestCompleted(long result, long responseCode, string[] headers, byte[] body) {
		GD.Print($"HTTP Response Code: {responseCode}");

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
				GD.Print("Redirecting to: " + redirectUrl);
				httpRequest.Request(redirectUrl);  // Re-issue the request
				return;
			} else {
				GD.PrintErr("Redirect received, but no Location header found.");
				return;
			}
		}

		// Normal response
		if (responseCode == 200)
		{
			string csv = System.Text.Encoding.UTF8.GetString(body);
			GD.Print("CSV data received:\n" + csv);
		
			string csvContent = System.Text.Encoding.UTF8.GetString(body);
			GD.Print("CSV fetched:\n", csvContent);
		
			ParseCsv(csvContent);
		
			if(urls.Count > 0) {
				currentIndex = 0;
				UpdateQRCode();
			} else {
				GD.PrintErr("No valid URL parsed from CSV.");
			}
		} else {
			GD.PrintErr($"HTTP Error: {responseCode}");
		}
	}
	
	private void ParseCsv(string csv) {
		urls.Clear();
		
		string[] lines = csv.Split('\n');
		
		foreach (var line in lines) {
			// returns string with specific char (\n) trimmed from it
			string trimmed = line.Trim();
			if(!string.IsNullOrEmpty(trimmed)) {
				urls.Add(trimmed);
			}
		}
		GD.Print("CSV parsed. ", urls.Count, " URLS found.");
	}
		
	public override void _Input(InputEvent @event) {
		if (@event is InputEventKey keyEvent && keyEvent.Pressed && !keyEvent.Echo) {
			if(urls.Count == 0) {
				return;
			}
			
			if (keyEvent.Keycode == Key.Right) {
				currentIndex = (currentIndex + 1) % urls.Count;
				UpdateQRCode();
			} else if (keyEvent.Keycode == Key.Left) {
				currentIndex = (currentIndex - 1 + urls.Count) % urls.Count;
				UpdateQRCode();
			}
		}
	}
	
	private void UpdateQRCode() {
		if(currentIndex < urls.Count && currentIndex >= 0) {
			string url = urls[currentIndex];
			GD.Print("Updating QR code to: ", url);
			var result = qrHelper.Call("generate_qr", url, 8);
			
			if(result.VariantType == Variant.Type.Object && result.As<Image>() is Image qrImage && !qrImage.IsEmpty()) {
			GD.Print("QR Image generated successfully!\n");

			ImageTexture texture = ImageTexture.CreateFromImage(qrImage);
			qrTexture.Texture = texture;
			} else {
				GD.PrintErr("Failed to generate QR image.");
			}
		}
	}
}
