import argparse
from pathlib import Path
import cv2
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

ARUCO_DICTS = {
    'DICT_4X4_50': cv2.aruco.DICT_4X4_50,
    'DICT_4X4_100': cv2.aruco.DICT_4X4_100,
    'DICT_5X5_50': cv2.aruco.DICT_5X5_50,
    'DICT_6X6_50': cv2.aruco.DICT_6X6_50,
    # Add more if needed
}

def generate_marker(dict_name, marker_id, pixels, out_path):
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICTS[dict_name])
    marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, pixels)
    # Add quiet zone (white border)
    border = int(0.15 * pixels)
    marker_img = cv2.copyMakeBorder(marker_img, border, border, border, border, cv2.BORDER_CONSTANT, value=255)
    cv2.imwrite(str(out_path), marker_img)
    return marker_img

def marker_to_pdf(marker_img, pdf_path, dict_name, marker_id):
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    page_w, page_h = A4
    # Marker size in mm
    marker_mm = 100
    marker_px = marker_img.shape[0]
    # Convert marker to RGB and save to temp PNG
    import tempfile
    import os
    tmp_png = tempfile.mktemp(suffix='.png')
    if len(marker_img.shape) == 2:
        rgb = cv2.cvtColor(marker_img, cv2.COLOR_GRAY2RGB)
    else:
        rgb = marker_img
    cv2.imwrite(tmp_png, rgb)
    # Compute size in points
    marker_pt = marker_mm * mm
    x = (page_w - marker_pt) / 2
    y = (page_h - marker_pt) / 2 + 20  # leave space for text
    c.drawImage(tmp_png, x, y, marker_pt, marker_pt)
    # Add text
    c.setFont("Helvetica", 12)
    c.drawCentredString(page_w/2, y - 18, f"ArUco {dict_name} id={marker_id}")
    c.setFont("Helvetica", 10)
    c.drawCentredString(page_w/2, y - 32, "Print at 100% scale. Verify marker is 100mm wide.")
    c.showPage()
    c.save()
    os.remove(tmp_png)

def main():
    parser = argparse.ArgumentParser(description="Generate ArUco marker PNGs and A4 PDFs.")
    parser.add_argument("--out-dir", required=True, help="Output directory for PNG/PDF files.")
    parser.add_argument("--ids", default="0,1,2,3,4,5", help="Comma-separated marker IDs.")
    parser.add_argument("--dict", default="DICT_4X4_50", choices=list(ARUCO_DICTS.keys()), help="ArUco dictionary.")
    parser.add_argument("--pixels", type=int, default=1200, help="Marker size in pixels (before border).")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = [int(x) for x in args.ids.split(",") if x.strip().isdigit()]
    dict_name = args.dict
    pixels = args.pixels

    for marker_id in ids:
        png_path = out_dir / f"aruco_{dict_name}_id_{marker_id}.png"
        pdf_path = out_dir / f"aruco_{dict_name}_id_{marker_id}.pdf"
        marker_img = generate_marker(dict_name, marker_id, pixels, png_path)
        marker_to_pdf(marker_img, pdf_path, dict_name, marker_id)
        print(f"Wrote {png_path} and {pdf_path}")

    # Write print instructions
    instr = out_dir / "PRINT_INSTRUCTIONS.txt"
    instr.write_text(
        """Print at 100% scale (no scaling, no fit-to-page).\n" +
        "Each marker should be exactly 100mm wide.\n" +
        "After printing, measure the marker width with a ruler.\n" +
        "If not exactly 100mm, adjust printer settings and reprint.\n" +
        "Do not laminate or cover with glossy material.\n" +
        "Use high-contrast matte paper for best results.\n" +
        """
    )
    print(f"Wrote {instr}")

if __name__ == "__main__":
    main()
