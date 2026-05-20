"""TouchDesigner experiment: replace comp_tabletop_calibration with a calibration grid image."""

import os
import struct
import zlib

print('GRID IMAGE REPLACEMENT STARTED')

# ============================================================================
# 1. Generate calibration grid image (BMP format, no external dependencies)
# ============================================================================

output_dir = 'data/aisi/calibration'
output_path = os.path.join(output_dir, 'table_module_grid.png')

# Create directory if needed
os.makedirs(output_dir, exist_ok=True)

# Image parameters
IMG_SIZE = 2000
ROI_CM = 500.0
TABLE_W_CM = 133.0
TABLE_D_CM = 67.0
PX_PER_CM = 4  # Scale: 500 cm -> 2000 px

cell_w_px = int(TABLE_W_CM * PX_PER_CM)  # 532 px
cell_d_px = int(TABLE_D_CM * PX_PER_CM)  # 268 px

# Create image array: RGBA format with transparent background
# Format: (y * IMG_SIZE + x) * 4 bytes for RGBA
# Initialize with fully transparent (alpha = 0)
img_data = bytearray([0, 0, 0, 0] * (IMG_SIZE * IMG_SIZE))

def set_pixel(x, y, r, g, b, a=255):
    """Set pixel at (x, y) to (r, g, b, a). PNG uses RGBA format."""
    if 0 <= x < IMG_SIZE and 0 <= y < IMG_SIZE:
        idx = (y * IMG_SIZE + x) * 4
        img_data[idx] = r
        img_data[idx + 1] = g
        img_data[idx + 2] = b
        img_data[idx + 3] = a

def draw_line(x0, y0, x1, y1, r, g, b, thickness=1):
    """Draw line using Bresenham algorithm with optional thickness."""
    def bresenham(x0, y0, x1, y1):
        """Bresenham line generator."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            yield x, y
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    # Draw main line and parallel offset lines for thickness
    for px, py in bresenham(x0, y0, x1, y1):
        set_pixel(px, py, r, g, b, a=255)
    
    # Add parallel lines for thickness
    if thickness > 1:
        # Perpendicular offset direction
        dx = x1 - x0
        dy = y1 - y0
        dist = (dx * dx + dy * dy) ** 0.5
        if dist > 0:
            # Perpendicular unit vector
            px_norm = -dy / dist
            py_norm = dx / dist
            # Draw offset lines
            for offset in range(1, thickness):
                ox = int(px_norm * offset)
                oy = int(py_norm * offset)
                for px, py in bresenham(x0 + ox, y0 + oy, x1 + ox, y1 + oy):
                    set_pixel(px, py, r, g, b, a=255)

def draw_cross(cx, cy, size, r, g, b):
    """Draw small cross at center."""
    draw_line(cx - size, cy, cx + size, cy, r, g, b, thickness=2)
    draw_line(cx, cy - size, cx, cy + size, r, g, b, thickness=2)

# Color definitions (RGB, all white for technical grid)
grid_color = (255, 255, 255)
axis_color = (255, 255, 255)

img_center = IMG_SIZE // 2

# ============================================================================
# Draw grid lines with exact spacing
# ============================================================================

# Draw vertical lines (spaced 532 px apart)
x = img_center
while x >= 0:
    draw_line(x, 0, x, IMG_SIZE - 1, *grid_color, thickness=2)
    x -= cell_w_px
x = img_center + cell_w_px
while x < IMG_SIZE:
    draw_line(x, 0, x, IMG_SIZE - 1, *grid_color, thickness=2)
    x += cell_w_px

# Draw horizontal lines (spaced 268 px apart)
y = img_center
while y >= 0:
    draw_line(0, y, IMG_SIZE - 1, y, *grid_color, thickness=2)
    y -= cell_d_px
y = img_center + cell_d_px
while y < IMG_SIZE:
    draw_line(0, y, IMG_SIZE - 1, y, *grid_color, thickness=2)
    y += cell_d_px

# Draw central X and Y axes (stronger with doubled thickness)
for i in range(IMG_SIZE):
    set_pixel(i, img_center, *axis_color)
    set_pixel(img_center, i, *axis_color)
    # Add parallel pixels for doubled thickness
    if img_center + 1 < IMG_SIZE:
        set_pixel(i, img_center + 1, *axis_color)
        set_pixel(img_center + 1, i, *axis_color)

# Draw small crosses at grid intersections
x = img_center
while x >= 0:
    y = img_center
    while y >= 0:
        draw_cross(x, y, 3, *grid_color)
        y -= cell_d_px
    y = img_center + cell_d_px
    while y < IMG_SIZE:
        draw_cross(x, y, 3, *grid_color)
        y += cell_d_px
    x -= cell_w_px

x = img_center + cell_w_px
while x < IMG_SIZE:
    y = img_center
    while y >= 0:
        draw_cross(x, y, 3, *grid_color)
        y -= cell_d_px
    y = img_center + cell_d_px
    while y < IMG_SIZE:
        draw_cross(x, y, 3, *grid_color)
        y += cell_d_px
    x += cell_w_px

# Write PNG file with RGBA support (using zlib compression from standard library)
def write_png(filepath, width, height, img_data_rgba):
    """Write PNG file with RGBA format and transparency support."""
    def png_chunk(chunk_type, data):
        """Create a PNG chunk: [length][type][data][crc]."""
        chunk_data = chunk_type + data
        crc = zlib.crc32(chunk_data) & 0xffffffff
        return struct.pack('>I', len(data)) + chunk_data + struct.pack('>I', crc)
    
    with open(filepath, 'wb') as f:
        # PNG signature
        f.write(b'\x89PNG\r\n\x1a\n')
        
        # IHDR chunk (image header)
        ihdr_data = struct.pack('>IIBBBBB',
            width, height,        # width, height
            8,                    # bit depth (8 bits per channel)
            6,                    # color type (6 = RGBA)
            0, 0, 0)              # compression, filter, interlace
        f.write(png_chunk(b'IHDR', ihdr_data))
        
        # IDAT chunk (image data) with zlib compression
        raw_data = bytearray()
        for y in range(height):
            raw_data.append(0)  # Filter type 0 (None) for each scanline
            for x in range(width):
                idx = (y * width + x) * 4
                raw_data.extend(img_data_rgba[idx:idx+4])
        
        compressed = zlib.compress(bytes(raw_data), 9)
        f.write(png_chunk(b'IDAT', compressed))
        
        # IEND chunk (image end)
        f.write(png_chunk(b'IEND', b''))

write_png(output_path, IMG_SIZE, IMG_SIZE, img_data)
print(f'Generated calibration grid image: {output_path}')

# ============================================================================
# 2. Set up TouchDesigner operators
# ============================================================================

target_path = '/project1/comp_tabletop_calibration'
container = op(target_path)
if not container:
    print('ERROR comp_tabletop_calibration not found')
else:
    # Clear children
    for child in list(container.children):
        try:
            child.destroy()
        except Exception as exc:
            print(f'Warning: failed to destroy {child.path}: {exc}')
    
    # Create Movie File In TOP
    moviefilein = container.create(moviefileinTOP, 'moviefilein_grid')
    try:
        moviefilein.par.file = output_path
    except Exception as e:
        print(f'Warning: could not set movie file path: {e}')
    
    # Create null TOP (output)
    null_render = container.create(nullTOP, 'null_render')
    null_render.inputConnectors[0].connect(moviefilein)
    
    print('GRID IMAGE REPLACEMENT FINISHED')
