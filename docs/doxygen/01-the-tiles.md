# The tiles

\image html tiles.png "Tile example"

The tiles may contain an image, a video, or other kind of visual data.

## The hitbox

On the left side of the tile, the black vertical zone enables to interact with the environment. It will be called the “hitbox” in the following.

Its color changes according to the current action :

| Color | Meaning |
|---|---|
| Dark red | The mouse is over the tile (only with desktop browsers). |
| Red | The tile is selected to be swapped with another one. |
| Green | The tile is selected for zoom mode or master-slave mode. |

## The stickers

On the right side, a vertical blank zone is designed to show the stickers of the tiles. These are colored squares representing ﬁlters or tags given to the tile. Each time they are shown, a legend is also displayed at the top of the screen.

## The handle

At the bottom left corner, a hand-shaped icon is dedicated to drag and drop actions.

Its color changes according to the current state of the tile:

| Color | Icon | Meaning |
|---|---|---|
| White | <img src="drag-handle-on.png" alt="White Handle" width="24"> | The tile may be drag-and-dropped. |
| Green | <img src="drag-handle-dragging.png" alt="Green Handle" width="24"> | The tile is currently draggable. |
| Gray | <img src="drag-handle-off.png" alt="Gray Handle" width="24"> | Drag-and-drop is not available at this time. |

# Interacting with the tiles

## Moving tiles

For the movements, the animation and animation speeds can be deﬁned in the conﬁg ﬁle.

### Swapping two individual tiles

The tiles are not exactly swapped, rather, the second one is moved next to the ﬁrst one, and the neighbouring tiles are re-arranged to preserve the coherence of the data. This action can be undone with the “Undo” button of the Global menu.

| Action | Behaviour on desktop browser | Behaviour on WildOS |
|---|---|---|
| 1. Hover over the ﬁrst tile. | The hitbox becomes dark red. | The hitbox stays black (the cursor is not detected by design). |
| 2. Click on the hitbox. | It becomes red. | It becomes red. |
| 3. Hover over the second tile. | Its hitbox becomes dark red. | Its hitbox stays black. |
| 4. Click on the hitbox of the second tile. | Done ! | Done ! |

### “Drag-and-drop”-ing tiles (only on desktop browsers)

This can be done when selecting the little hand at the bottom left corner of the tile and moving it to its destination. It is diﬀerent from the ﬁrst case, as two tiles will be swapping their position.

When drag and dropping a transparent tile, the tile is ovelapped on the underlaying tile, enabling the user to compare diﬀerent but related data.

Options in `config_default.js` as well as in the option menu enable to unload the tile when dragging (“Move only a border”) or move without animation.

### Swapping entire lines or columns

The two last options in the individual menu of each tile allow the user to swap the line (resp. column) of this tile with another one, by clicking on the icon of the tile in the destination line (resp. column). See documentation on these icons (in the Tile menu section) for more information.

[Next: Global menu](@ref md_02-global-menu)
