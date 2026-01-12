# LLM-OS TUI Usage Guide

## Copying Text from the TUI

The TUI (Terminal User Interface) captures keyboard input, so standard Ctrl+C doesn't work for copying. Here are the solutions:

### Method 1: Mouse Selection (Recommended)

**For GNOME Terminal / Debian default terminal:**
1. **Select text** with your mouse (click and drag)
2. **Copy** with `Shift+Ctrl+C` (or right-click → Copy)
3. **Paste** with `Shift+Ctrl+V` (or right-click → Paste)

**For other terminals:**
- **xterm**: Select with mouse, middle-click to paste
- **kitty**: Select with mouse, Ctrl+Shift+C to copy
- **alacritty**: Select with mouse, Ctrl+Shift+C to copy

### Method 2: Terminal Scrollback

1. Press `Shift+Page Up` to scroll up
2. Select text with mouse
3. Copy with `Shift+Ctrl+C`

### Method 3: Use --no-ui Mode

If you need frequent copy/paste, use CLI mode:

```bash
# Run without TUI
./launch.sh --no-ui

# Or with specific command
./launch.sh -c "list files"
```

In CLI mode, regular Ctrl+C copy/paste works.

## TUI Keyboard Shortcuts

- `Ctrl+D` or `/exit` - Exit LLM-OS
- `/help` - Show help
- `/status` - Show system status
- `/clear` - Clear conversation context
- `Up/Down arrows` - Navigate command history
- `Shift+Page Up/Down` - Scroll response area

## Common Issues

### Issue: Ctrl+C exits the program

**Solution**: Use `Shift+Ctrl+C` for copying, or type `/exit` to quit properly.

### Issue: Can't select text

**Solution**: Make sure your terminal has mouse mode enabled. For GNOME Terminal:
1. Edit → Preferences
2. Select your profile
3. Check "Select text with mouse"

### Issue: Copying doesn't work

**Solution**: Your terminal emulator might need different key combinations:
- Try `Shift+Ctrl+C`
- Try `Ctrl+Insert`
- Check your terminal's preferences/settings

## Alternative: Use Log Viewer

All responses are logged, so you can also view and copy from logs:

```bash
# View recent interactions
./view-logs.sh --category user --since 10m

# Copy from terminal output (this is plain text)
```

## Recommended Workflow

1. **Interact in TUI** for real-time responses
2. **Copy from logs** when you need text:
   ```bash
   ./view-logs.sh --category user --tail 5
   ```
3. **Use --no-ui** for scripting or automation

