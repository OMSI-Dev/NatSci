# Next steps: Modify the main scene 

AS of now, the main scene automatically displays the current assets in the scene. By default (on page load, and without a piece registered) these assets should be hidden: PersonHighlight (Interest), CloudHighlight (Topic), HouseHighlight (Group)

When a piece is registered in a specific category, unhide the specific asset associated with it. 

# Scene Transition: Results

Once all pieces are registered, there is only one transition to occur (from Main.tscn to Results.tscn) 

In the transition, immediately show the Results Background, and do a left-to-right wipe reveal with the Results pill
