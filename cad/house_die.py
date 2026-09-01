"""
Generate a 3D-printable extrusion die: a flat plate with a "house" shaped
through-cutout (pointed roof, straight walls, rounded base corners).

All dimensions in millimetres.

Cutout profile
    width (wall to wall)          : 27.5   (2.75 cm)
    base to eaves ("to roof")     : 17.5   (1.75 cm)
    base to roof apex (total)     : 30.0   (3.00 cm)
    base corner fillet radius     :  5.0  (--fillet 0 for sharp corners)

Die plate
    110 x 110 x 10

Usage: python3 cad/house_die.py [--fillet R] [--eaves H] [--apex H]
              [output.stp|output.stl ...]

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


def house_profile(fillet=BASE_FILLET, eaves=EAVES_HEIGHT, apex=TOTAL_HEIGHT):
    """Closed 2D sketch of the cutout, centred on its bounding box.

    A fillet of 0 leaves the base corners sharp. The apex must clear the eaves,
    otherwise the roof would slope down into the opening instead of peaking.
    """
    if apex <= eaves:
        raise ValueError(
            f"apex {apex} must be above the eaves {eaves}; the roof cannot "
            f"peak below the walls it sits on"
        )
    half_w = WIDTH / 2.0
    y0 = -apex / 2.0                    # base line
    y_eaves = y0 + eaves
    y_apex = y0 + apex

    points = [
        (-half_w, y0),
        (half_w, y0),
        (half_w, y_eaves),
        (0.0, y_apex),
        (-half_w, y_eaves),
    ]

    sketch = cq.Sketch().polygon(points)
    if fillet > 0:
        sketch = sketch.vertices("<Y").fillet(fillet)   # the two base corners
    return sketch.reset()


def build(fillet=BASE_FILLET, eaves=EAVES_HEIGHT, apex=TOTAL_HEIGHT):
    profile = house_profile(fillet, eaves, apex)

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
    args = sys.argv[1:]
    def take(flag, default):
        if flag not in args:
            return default
        i = args.index(flag)
        value = float(args[i + 1])
        del args[i:i + 2]
        return value

    fillet = take("--fillet", BASE_FILLET)
    eaves = take("--eaves", EAVES_HEIGHT)
    apex = take("--apex", TOTAL_HEIGHT)

    outputs = args or ["house_die.stp", "house_die.stl"]
    die = build(fillet, eaves, apex)
    for path in outputs:
        export(die, path)
    bb = die.val().BoundingBox()
    print(f"bounding box: {bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f} mm")
    print(f"volume: {die.val().Volume():.1f} mm^3")
