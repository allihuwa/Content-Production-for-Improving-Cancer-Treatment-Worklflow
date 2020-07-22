# Run this cell to load a file from a URL.
# You can load your own data by changing inputs of downloadFromURL.
# Any questions? Write us on the Slicer forum: https://discourse.slicer.org
slicer.mrmlScene.Clear()

volume = slicernb.downloadFromURL(
    uris="https://github.com/allihuwa/Content-Production-for-Improving-Cancer-Treatment-Worklflow/raw/master/pelvisvolume.nrrd",
    fileNames="pelvisvolume.nrrd",
    nodeNames="pelvisvolume")[0]

slicernb.showVolumeRendering(volume)

# Enable volume cropping
displayNode = slicer.modules.volumerendering.logic().GetFirstVolumeRenderingDisplayNode(volume)
displayNode.SetCroppingEnabled(True)
roiNode = displayNode.GetROINode()

# 3D view display
slicernb.reset3DView()
from ipywidgets import interact
@interact(roll=(-90.0,90.0,5), pitch=(-90.0,90.0,5), yaw=(-180.0,180.0,5), cropx=(0,70,5), cropy=(0,120,5), cropz=(0, 80, 5))
def update(roll=0, pitch=0, yaw=0, cropx=70, cropy=120, cropz=80):
    roiNode.SetRadiusXYZ([cropx, cropy, cropz])
    return slicernb.View3DDisplay(0, orientation=[roll, pitch, yaw])