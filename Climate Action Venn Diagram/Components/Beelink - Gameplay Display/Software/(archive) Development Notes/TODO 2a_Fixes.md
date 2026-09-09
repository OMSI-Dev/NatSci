# Frontend Fixes

1) The loading transition does not presently show. 
2) Generated QR codes do not fit within the bounds of their Godot element, particularly more complex/dense QR codes. 

# (Repeat) Scene Transition: Loading

Once all 3 unique pieces are registered, trigger a transition (from Main.tscn to Results.tscn). This is the only linear transition. 

In this transition:
1) show the LoadingBackground
2) Animate a left-to-right wipe-in reveal (animated mask?) with the ResultsPill, emulate a loading bar. 
3) Animate a wipe-out transition of the entire 'Loading' layer to reveal the shown ResultsBackground


