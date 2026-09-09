using Godot;

/*
* Generates QR codes locally (via the qr_code addon) for the national and
* local organization links of the current outcome. No network access.
*
* GameController calls SetUrls() when the results phase begins.
* Expected children: QRTextureNational, QRTextureLocal (TextureRect),
* QRCodeHelper (Node running Scripts/QRCodeHelper.gd).
*/
public partial class QRGenerator : Node2D
{
	private TextureRect qrTextureNational;
	private TextureRect qrTextureLocal;
	private Node qrHelper;

	public override void _Ready()
	{
		qrTextureNational = GetNodeOrNull<TextureRect>("QRTextureNational");
		qrTextureLocal = GetNodeOrNull<TextureRect>("QRTextureLocal");
		qrHelper = GetNodeOrNull("QRCodeHelper");

		if (qrHelper == null) {
			GD.PrintErr("[QRGenerator] QRCodeHelper child node not found.");
		}
	}

	public void SetUrls(string nationalUrl, string localUrl)
	{
		Generate(nationalUrl, qrTextureNational, "National");
		Generate(localUrl, qrTextureLocal, "Local");
	}

	private void Generate(string url, TextureRect target, string label)
	{
		if (qrHelper == null || target == null || string.IsNullOrEmpty(url)) {
			return;
		}

		var result = qrHelper.Call("generate_qr", url, 8);
		if (result.VariantType == Variant.Type.Object
			&& result.As<Image>() is Image qrImage && !qrImage.IsEmpty()) {
			target.Texture = ImageTexture.CreateFromImage(qrImage);
			GD.Print($"[QRGenerator] {label} QR generated for: {url}");
		} else {
			GD.PrintErr($"[QRGenerator] Failed to generate {label} QR for: {url}");
		}
	}
}
