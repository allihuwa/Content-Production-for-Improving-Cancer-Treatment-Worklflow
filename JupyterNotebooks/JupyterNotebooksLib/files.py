import slicer

def getFileNameFromURL(url):
    import urllib
    req = urllib.request.Request(url, method='HEAD')
    r = urllib.request.urlopen(req)
    filename = r.info().get_filename()
    if not filename:
      # No filename is available, try to get it from the url
      import os
      from urllib.parse import urlparse
      parsedUrl = urlparse(url)
      filename = os.path.basename(parsedUrl.path)
    return filename

def downloadFromURL(uris=None, fileNames=None, nodeNames=None, checksums=None, loadFiles=None,
  customDownloader=None, loadFileTypes=None, loadFileProperties={}):
  """Download data from custom URL with progress bar.
  See API description in SampleData.downloadFromURL.
  """
  import SampleData
  sampleDataLogic = SampleData.SampleDataLogic()

  try:
    from ipywidgets import IntProgress
    from IPython.display import display
    progress = IntProgress()
  except ImportError:
    progress = None

  def reporthook(msg, level=None):
    # Download will only account for 90 percent of the time
    # (10% is left for loading time).
    progress.value=sampleDataLogic.downloadPercent*0.9

  if progress:
    sampleDataLogic.logMessage = reporthook
    display(progress) # show progress bar

  computeFileNames = not fileNames
  computeNodeNames = not nodeNames
  if computeFileNames or computeNodeNames:
    urisList = uris if type(uris) == list else [uris]
    if computeFileNames:
      fileNames = []
    else:
      filenamesList = fileNames if type(fileNames) == list else [fileNames]
    if computeNodeNames:
      nodeNames = []
    else:
      nodeNamesList = nodeNames if type(nodeNamesList) == list else [nodeNames]
    import os
    for index, uri in enumerate(urisList):
      if computeFileNames:
        fileName = getFileNameFromURL(uri)
        fileNames.append(fileName)
      else:
        fileName = fileNames[index]
      if computeNodeNames:
        fileNameWithoutExtension, _ = os.path.splitext(fileName)
        nodeNames.append(fileNameWithoutExtension)
        
  if type(uris) != list:
    if type(fileNames) == list:
      fileNames = fileNames[0]
    if type(nodeNames) == list:
      nodeNames = nodeNames[0]
        
  downloaded = sampleDataLogic.downloadFromURL(uris, fileNames, nodeNames, checksums, loadFiles,
    customDownloader, loadFileTypes, loadFileProperties)

  if progress:
    progress.layout.display = 'none' # hide progress bar
    
  return downloaded[0] if len(downloaded) == 1 else downloaded

def localPath(filename=None):
  import os
  notebookDir = os.path.dirname(notebookPath())
  if not filename:
    return notebookDir
  else:
    return os.path.join(notebookDir, filename)

def notebookPath(verbose=False):
  """Returns the absolute path of the Notebook or None if it cannot be determined
  NOTE: works only when the security is token-based or there is also no password.
  """
  # Code is extracted from notebook\notebookapp.py to avoid requiring installation of notebook on server

  import urllib.request
  import json
  import io, os, re, sys

  def check_pid(pid):

    def _check_pid_win32(pid):
      import ctypes
      # OpenProcess returns 0 if no such process (of ours) exists
      # positive int otherwise
      return bool(ctypes.windll.kernel32.OpenProcess(1,0,pid))

    def _check_pid_posix(pid):
      """Copy of IPython.utils.process.check_pid"""
      try:
        os.kill(pid, 0)
      except OSError as err:
        if err.errno == errno.ESRCH:
          return False
        elif err.errno == errno.EPERM:
          # Don't have permission to signal the process - probably means it exists
          return True
        raise
      else:
        return True

    if sys.platform == 'win32':
      return _check_pid_win32(pid)
    else:
      return _check_pid_posix(pid)

  def list_running_servers():
      # Iterate over the server info files of running notebook servers.
      # Given a runtime directory, find nbserver-* files in the security directory,
      # and yield dicts of their information, each one pertaining to
      # a currently running notebook server instance.
      runtime_dir = os.path.dirname(connection_file)

      for file_name in os.listdir(runtime_dir):
        if not re.match('nbserver-(.+).json', file_name):
          continue
        if verbose: print(file_name)
        with io.open(os.path.join(runtime_dir, file_name), encoding='utf-8') as f:
          info = json.load(f)
        # Simple check whether that process is really still running
        if ('pid' in info) and check_pid(info['pid']):
          yield info

  connection_file = slicer.modules.jupyterkernel.connectionFile

  kernel_id = connection_file.split('-', 1)[1].split('.')[0]

  for srv in list_running_servers():
    try:
      if verbose: print(srv)
      if srv['token']=='' and not srv['password']:  # No token and no password, ahem...
        req = urllib.request.urlopen(srv['url']+'api/sessions')
      else:
        req = urllib.request.urlopen(srv['url']+'api/sessions?token='+srv['token'])
      sessions = json.load(req)
      if verbose: print("sessions: "+repr(sessions))
      for sess in sessions:
        if sess['kernel']['id'] == kernel_id:
          return os.path.join(srv['notebook_dir'],sess['notebook']['path'])
    except Exception as e:
      if verbose: print("exception: "+str(e))
      pass  # There may be stale entries in the runtime directory

  return None

def notebookSaveCheckpoint():
    """Save a checkpoint of current notebook. Returns True on success."""
    try:
      from IPython.display import Javascript
      from IPython.display import display
    except ModuleNotFoundError:
      import logging
      logging.error("notebookSaveCheckpoint requires ipywidgets. It can be installed by running this command:\n\n    pip_install('ipywidgets')\n")
      return False

    script = '''
    require(["base/js/namespace"],function(Jupyter) {
        Jupyter.notebook.save_checkpoint();
    });
    '''
    display(Javascript(script))
    return True

def notebookExportToHtml(outputFilePath=None):
    """Export current notebook to HTML.
    If outputFilePath is not specified then filename will be generated from the notebook filename
    with current timestamp appended.
    It returns full path of the saved html file.
    It requires nbformat and nbconvert packages. You can use this command to install them:
        pip_install("nbformat nbconvert")
    """
    try:
      import nbformat
      from nbconvert import HTMLExporter
    except ModuleNotFoundError:
      import logging
      logging.error("notebookExportToHtml requires nbformat and nbconvert. They can be installed by running this command:\n\n    pip_install('nbformat nbconvert')\n")

    import datetime, json, os

    notebook_path = notebookPath()

    # Generate output file path from notebook name and timestamp (if not specified)
    if not outputFilePath:
      this_notebook_name = os.path.splitext(os.path.basename(notebook_path))[0]
      save_timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
      save_file_name = this_notebook_name + "_" + save_timestamp + ".html"
      notebooks_save_path = os.path.dirname(notebook_path)
      outputFilePath = os.path.join(notebooks_save_path, save_file_name)

    with open(notebook_path, mode="r") as f:
        file_json = json.load(f)
        
    notebook_content = nbformat.reads(json.dumps(file_json), as_version=4)

    html_exporter = HTMLExporter()
    (body, resources) = html_exporter.from_notebook_node(notebook_content)

    f = open(outputFilePath, 'wb')
    f.write(body.encode())
    f.close()

    return outputFilePath

def installExtensions(extensionNames):
    success = True
    import logging
    emm = slicer.app.extensionsManagerModel()
    installedExtensions = []
    failedToInstallExtensions = []
    notFoundExtensions = []
    for extensionName in extensionNames:
        if emm.isExtensionInstalled(extensionName):
            continue
        md = emm.retrieveExtensionMetadataByName(extensionName)
        if not md or 'extension_id' not in md:
            notFoundExtensions.append(extensionName)
            continue
        if not emm.downloadAndInstallExtension(md['extension_id']):
            failedToInstallExtensions.append(extensionName)
            continue
        installedExtensions.append(extensionName)

    if notFoundExtensions:
        logging.warning("Extensions not found: " + ", ".join(notFoundExtensions))
        success = False
    if failedToInstallExtensions:
        logging.warning("Extensions failed to install: " + ", ".join(failedToInstallExtensions))
        success = False
    if installedExtensions:
        print("Extensions installed: " + ", ".join(installedExtensions))
        logging.warning("Restart the kernel to make the installed extensions available in this notebook.")

    return success
