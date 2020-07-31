# Run this cell (Shift+Enter) to show application here
import JupyterNotebooksLib as slicernb
slicernb.AppWindow(contents='full')

#download file and load volume rendering to the scene
slicer.mrmlScene.Clear()

volume = slicernb.downloadFromURL(
    uris="https://github.com/allihuwa/Content-Production-for-Improving-Cancer-Treatment-Worklflow/raw/master/pelvisvolume.nrrd",
    fileNames="pelvisvolume.nrrd",
    nodeNames="pelvisvolume")[0]

slicernb.showVolumeRendering(volume)

#Enable segmentation and add sphere to the segmentation node

segmentationNode = slicer.vtkMRMLSegmentationNode()
slicer.mrmlScene.AddNode(segmentationNode)
segmentationNode.CreateDefaultDisplayNodes() # only needed for display
segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(volume)


#Sphere 1
tumorSeed = vtk.vtkSphereSource()
tumorSeed.SetCenter(0, -50, 3)
tumorSeed.SetRadius(10)
tumorSeed.Update()
segmentationNode.AddSegmentFromClosedSurfaceRepresentation(tumorSeed.GetOutput(), "Tumor", [1.0,0.0,0.0])


# Compute histogram of intensities corresponding to sphere location 
#with respect to the volume rendering location of intersection
################################################

labelValue = 1  # label value of first segment

# Get segmentation as labelmap volume node
labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, labelmapVolumeNode, volume)

# Extract all voxels of the segment as numpy array
volumeArray = slicer.util.arrayFromVolume(volume)
labelArray = slicer.util.arrayFromVolume(labelmapVolumeNode)
segmentVoxels = volumeArray[labelArray==labelValue]

# Compute histogram
import numpy as np
histogram = np.histogram(segmentVoxels, bins=50)

# Plot histogram
################################################

slicer.util.plot(histogram, xColumnIndex = 1)		


