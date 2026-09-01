"""
Generate a 3D-printable extrusion die: a flat plate with a "house" shaped
through-cutout (pointed roof, straight walls, rounded base corners).

All dimensions in millimetres.

Cutout profile
    width (wall to wall)          : 27.5   (2.75 cm)
    base to eaves ("to roof")     : 17.5   (1.75 cm)
    base to roof apex (total)     : 30.0   (3.00 cm)
    base corner fillet radius     :  5.0

Die plate
    110 x 110 x 10

Usage: python3 cad/house_die.py [output.stp|output.stl ...]

The export format is chosen from each output file's extension; with no
arguments both house_die.stp and house_die.stl are written.
"""

import sys

import cadquery as cq

# --- cutout profile ---------------------------------------------------------
WIDTH = 27.5          # overall width of the cutout
EAVES_HEIGHT = 17.5   # base -> top of the straight side walls
TOTAL_HEIGHT = 30.0   # base -> roof apex (apex sits on the centre line)
BASE_FILLET = 5.0     # rounding of the two base corners

# --- die plate --------------------------------------------------------------
PLATE_X = 110.0
PLATE_Y = 110.0
PLATE_T = 10.0


def house_profile():
    """Closed 2D sketch of the cutout, centred on its bounding box."""
    half_w = WIDTH / 2.0
    y0 = -TOTAL_HEIGHT / 2.0            # base line
    y_eaves = y0 + EAVES_HEIGHT
    y_apex = y0 + TOTAL_HEIGHT

    points = [
        (-half_w, y0),
        (half_w, y0),
        (half_w, y_eaves),
        (0.0, y_apex),
        (-half_w, y_eaves),
    ]

    return (
        cq.Sketch()
        .polygon(points)
        .vertices("<Y")                 # the two base corners
        .fillet(BASE_FILLET)
    )


def build():
    profile = house_profile()

    cutter = (
        cq.Workplane("XY")
        .placeSketch(profile)
        .extrude(PLATE_T, both=True)    # overshoot so the cut goes right through
    )

    plate = cq.Workplane("XY").box(PLATE_X, PLATE_Y, PLATE_T)
    return plate.cut(cutter)


# Mesh resolution used for STL; fine enough that the fillets and the flat
# walls print true to the STEP geometry.
STL_TOLERANCE = 0.01
STL_ANGULAR_TOLERANCE = 0.1


def export(die, path):
    if path.lower().endswith(".stl"):
        cq.exporters.export(
            die,
            path,
            cq.exporters.ExportTypes.STL,
            tolerance=STL_TOLERANCE,
            angularTolerance=STL_ANGULAR_TOLERANCE,
        )
    else:
        cq.exporters.export(die, path, cq.exporters.ExportTypes.STEP)
    print(f"wrote {path}")


if __name__ == "__main__":
    outputs = sys.argv[1:] or ["house_die.stp", "house_die.stl"]
    die = build()
    for path in outputs:
        export(die, path)
    bb = die.val().BoundingBox()
    print(f"bounding box: {bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f} mm")
    print(f"volume: {die.val().Volume():.1f} mm^3")
