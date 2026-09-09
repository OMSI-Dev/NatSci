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
		qrTextureLocal = GetNodeOrNull<TextureRect>("QRTextureLocal")
			?? GetNodeOrNull<TextureRect>("QRTextureLocal2");
		qrHelper = GetNodeOrNull("QRCodeHelper");

		// Dense QR codes produce images larger than the boxes laid out in the
		// scene; by default a TextureRect grows to the texture's size. Scale
		// the image into the box instead, and keep the modules crisp.
		foreach (TextureRect rect in new[] { qrTextureNational, qrTextureLocal }) {
			if (rect != null) {
				rect.ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize;
				rect.StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered;
				rect.TextureFilter = TextureFilterEnum.Nearest;
			}
		}

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
