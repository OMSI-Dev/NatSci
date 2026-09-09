# General Rules

Refer to the Godot scenes 'Main.tcsn' and 'Results.tcsn' 

# Current State

The main scene automatically displays the current assets in the scene. 

# Implementation 
By default (on page load, and without a piece registered) these assets should be hidden: PersonHighlight (Interest), CloudHighlight (Topic), HouseHighlight (Group)

When a piece is registered in a specific category, unhide the specific asset associated with it. Make dev commands keys '1', '2', and '3' to register pieces 0x01, 0x0D, and 0x19.

# Scene Transition: Loading

Once all 3 unique pieces are registered, trigger a transition (from Main.tscn to Results.tscn). This is the only linear transition. 

In this transition:
1) show the LoadingBackground
2) Animate a left-to-right wipe-in reveal (animated mask?) with the ResultsPill, emulate a loading bar. 
3) Animate a wipe-out transition of the entire 'Loading' layer to reveal the shown ResultsBackground

# Scene: Results

The ResultBackground should already be showing and revealed after the 'Loading' layer has its' transition out. 

The following components need to be populated via code:
- NationalLabel - name of the national org (NationalOrg.Name)
- NationalDesc - description of national org (NationalOrg.Description)
- LocalLabel - name of local org (SelectedLocalOrg.Name)
- LocalDesc - description of local org (SelectedLocalOrg.Description)

AS well as their Spanish counterpart descriptions must be stored for displaying. The Spanish displays will show upon a 'L' keypress.

Nothing should be touched with the design/font/color. All of this is already configured in the UI. The text does have to fit within the bounds of the precofigured text boxes, but no changing of the font size. 

# QR Generation
In the Results screen, the QRTextureNational and QRTextureLocal should display QR codes of the respective National and Local URLs. 

Existing QR generation scripts present in the original versions of the code. 





