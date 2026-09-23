shader_type canvas_item;

// Horizontal wipe in screen space. `left`/`right` bound the wipe region in
// SCREEN_UV coordinates (0-1 = full screen; a sprite's own extent for a
// loading-bar fill). reveal=true shows pixels left of the moving edge
// (wipe-in); reveal=false shows pixels right of it (wipe-out).
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform float left = 0.0;
uniform float right = 1.0;
uniform bool reveal = true;

void fragment() {
	float edge = mix(left, right, progress);
	bool shown = reveal ? (SCREEN_UV.x <= edge) : (SCREEN_UV.x > edge);
	if (!shown) {
		discard;
	}
}
