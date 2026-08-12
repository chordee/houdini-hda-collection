"""Checks every file in the sequence before the clip layer is written.

Time samples are not looked at while the node cooks. Reading a file to find them
costs about a millisecond, and the Load Layer releases the bgeo once it has
copied it, so the read is never cached -- on a node that exists to be quick, a
500 frame sequence would spend half a second of every stage evaluation on it.
The cook-time validation therefore covers only the Primitive path, which it can
answer from the stage it already holds.

That makes this the one place sample frames are verified, so it checks every
frame rather than just the template. A sequence written unevenly, some frames
through a usdconfigure Sample Frame and some not, would otherwise reach the clip
with frames that resolve to nothing.

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
