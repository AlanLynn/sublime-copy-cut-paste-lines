## Copy Cut and Paste Lines - Package for Sublime Text

The purpose of this package is to improve your coding efficiency.

It does that by replacing the default Copy, Cut, and Paste with new versions that operate on full lines of code. Because moving lines of codes is such a common operation, making it even a little easier has a big benefit.

*Wait, I don't want to copy/cut the whole line every time!*  
Don't worry, selections within a single line are treated normally, copying and cutting just the selection, not the whole line.

And in case you need to use the original versions of copy/cut/paste, they are bound to new shorctuts.  
Original Copy: <kbd>Ctrl+Alt+C</kbd> Original Cut: <kbd>Ctrl+Alt+X</kbd> Original Paste: <kbd>Ctrl+Alt+V</kbd>  
If you don't like these bindings, set your own in Key Bindings - User. (See section [Rebinding Keys](#rebinding-keys).)


### Demonstration

Cutting and pasting lines:  
![Demonstration gif](http://alanlynn.github.io/copy-cut-paste-lines-sublime/demo.gif)


### Potential Downsides

* There are some scenarios when you don't want to cut/copy/paste lines, for example using rectangular selection. In this case, use the rebound shortcuts listed above.
* No entries are created in the paste history list.


### How to Install

1. Install [Package Control](https://packagecontrol.io/installation) if you do not already have it.
2. In Sublime Text, open the Package Control command pallete. (Preferences → Package Control)
3. Select "Install Package".
4. Search for Copy, Cut, and Paste Lines and select it.


### Rebinding Keys

If you don't like the default key bindings, paste the code below into *Key Bindings - User* and edit the keys to your liking.

```json
// Key bindings for the "improved" copy, cut, paste, and duplicate commands:
{ "keys": ["ctrl+c"], "command": "ccpl_copy" },
{ "keys": ["ctrl+x"], "command": "ccpl_cut" },
{ "keys": ["ctrl+v"], "command": "ccpl_paste" },
{ "keys": ["ctrl+shift+d"], "command": "ccpl_duplicate" },
// Key bindings for the original copy, cut, paste, and duplicate commands:
{ "keys": ["ctrl+alt+c"], "command": "copy" },
{ "keys": ["ctrl+alt+x"], "command": "cut" },
{ "keys": ["ctrl+alt+v"], "command": "paste" },
{ "keys": [""], "command": "duplicate_lines" },
```
