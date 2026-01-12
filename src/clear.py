# Clear the currently active display
import sys
import genlib as gl

print()

# Get platform configuration
cfg = gl.get_board_config()
keys = cfg.keys()

# Get DAL implementation
if 'display_type' not in keys:
    print('Display type not configured')
    sys.exit(1)
dal_module = f'dal_{cfg["display_type"]}'
if not gl.module_available(dal_module):
    print(f'DAL implementation {dal_module} not available')
    sys.exit(1)

# Initialize display
display = __import__(dal_module).DAL()

# Clear and update the display
if display is not None:
    display.fill(display.BLACK)
    display.show()
