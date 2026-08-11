"""Checks the whole sequence before the clip layer is written.

The per-cook validation inside the asset only looks at the template frame,
because opening every file in the range costs about a millisecond each and this
node cooks interactively -- a 500 frame sequence would spend half a second on
the scan every time the stage is evaluated.

A sequence written unevenly, some frames through a usdconfigure Sample Frame and
some not, passes the template check and leaves frames in the clip that resolve to
nothing. That case is worth catching, so the exhaustive scan runs here instead:
once, at the moment the layer is actually written.

Missing files are left alone; the Load Layer upstream already reports those.
"""
import hou
from pxr import Sdf

node = hou.pwd()
asset = node.node('..')

primpath = asset.parm('primpath').evalAsString().strip()
first = asset.parm('frame_range1').eval()
last = asset.parm('frame_range2').eval()

for frame in range(first, last + 1):
    path = asset.parm('filepath').evalAsStringAtFrame(frame)
    layer = Sdf.Layer.FindOrOpen(path)
    if layer is None:
        continue

    sampled = []

    def visit(spec_path, layer=layer, sampled=sampled):
        if sampled:
            return
        spec = layer.GetAttributeAtPath(spec_path)
        if spec is not None and spec.HasInfo('timeSamples'):
            sampled.append(1)

    layer.Traverse(Sdf.Path(primpath), visit)

    if not sampled:
        raise hou.NodeError(
            'This file carries no USD time samples, so its frame would resolve '
            'to nothing: %s' % path)
