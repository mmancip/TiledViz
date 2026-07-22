# Conﬁguration

## Default conﬁguration

A default conﬁguration is loaded by TiledViz from the `config_default.js` ﬁle. It contains the following parameters * Colors: for the diﬀerent stickers (for ﬁlters and tags), and markers of state (selected tile, tile to be zoomed, …) * Tile conﬁguration: how to use the parameters contained in `tiles.js` * Behavioural constants: number of tiles, of columns, should they be ﬁxed, spaces between tiles, …

## Custom conﬁguration

In order to specify custom parameters and to enhance the user experience, it is possible to add in the Case folder a copy of `config_default.js` (to be named `config.js`). It is not mandatory to add in this custom ﬁle all the parameters from the default conﬁguration ﬁle, but one has to be cautious of the syntax when writing those custom parameters.

| In `config_default.js` | In `config.js` | Result in TiledViz |
|---|---|---|
| `param_1 = value_1` | `param_1 = value_2` | `param_1 = value_2` |
| `param_1 = value_1` | Nothing or no `config.js` | `param_1 = value_1` |

[Previous: Tags menu and Zoom Global Menu](03-sub-menu.md)
