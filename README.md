# Google Earth 3D Map Model Importer & Lily Capture Merger  & Lily Texture Pack Automation 
This scripting solution I developed has one primary goal and that is to automate a very time-consuming job of importing RenderDoc files into Blender using the MapsModelImporter addon (https://github.com/eliemichel/MapsModelsImporter), it also will automate two more addon processes if you have them called Lily Texture Packer and Lily Capture Merger.

* The script you need to run is the import_merge_pack_textures_join.py this can be ran inside the Blender scripting interface or can be run using the command line.
* Before running the script be sure to modify the following:
  * The filepaths in the constants.py to match the RenderDoc file location and provide the filepaths where you would like files to be created or a filepath to ones already made.
  * The import_merge_pack_textures_join.py also has a few variables to edit to your own personal needs, see the comments around those variables for further information on the process
  * Your RDC files need to be in order if you have the Lily Capture Merger Addon as for the merges to be successful there must be overlapping geometry and materials
  * If file space is an issue you can enable the delete variable 'delete_rdc_files' in import_merge_pack_textures_join.py to True and this will delete the files afrer import, so make a backup of these files if you plan to reuse them or you are testing them
  * I have added a text file to give guidence on what to enter into the command line and perform these tasks in the background, with a prerequisete of the .blend file already existing when running this
  * The location of the scripts folder must be in the same file path as the .blend file or you can move it else where and edit the path to the file in 'import_merge_pack_textures_join.py' at'if __name__ == '__main__':' to match the correct path
  * Lastly there is a known issue where certain RDC files will cause the program to exit early where the satallite imagery is coming from another source other than Google and currently trying to fix this issue by handling these import errors

#### Important Pre-Release Information
**This Scripting solution has been tested in Blender versions 3.4.1 to 3.6.0, it is likely to run in earlier versions, but currently tests have not been conducted in these versions. Feel free to post versions that you have used for this solution where supported versions are not listed or issues on the current Blender version.**

**Issues on Blender versions that are outside the addons requirements or supported versions will not be considered as an issue for this script**

_There are a few methods in the two shared script .py files that aren't being called in the 'import_merge_pack_textures_join.py' as they are for another script I am developing to create geometry meshes from this first script to clean up some of the bad geometry that comes from these imports and make a lower poly version of the imported model from the first script. These are due to be removed in the release version as I will create two standalone release packages for these scripting solutions._

_As this is a pre-release version not all code comments are a 100% accurate due multiple itterations created to get this to work correctly and will be addressed in the next version, if any bugs or issues are found please submit a bug and I will do my best to address them._

_As this is my first official public pre-release solution into a Blender Python scripting solution please feel free to leave comments or recomendations to improve it, and I will do my best to address them as quickly as possible._

## This script is in the pre-release stage so issues and bugs may be present or unaccounted for
**However I have conducted extensive testing on it and have only found one known bug, and is stable to use for most cases**

In the Image below you can see the capture is about to take a capture from a U.S. Navy source and will cause Maps Model Importer to fail
![image](https://github.com/sir306/GoogleEarth_MapImport_CapMerge_TexPack_Automation/assets/40708936/95dfbca7-9b7d-4154-b633-3c26666fabf8)

A Link to this example has been provided:
[](url)https://earth.google.com/web/@-43.55529439,172.74939961,3.19291048a,808.72012098d,35y,156.51603316h,65.97568547t,0r
### When using this solution my only requirement is that you cite my name Nicholas Harding and cite this repository
### You also need to refer to further citations and uses from the addons creator @https://github.com/eliemichel when using his addons for your solution

