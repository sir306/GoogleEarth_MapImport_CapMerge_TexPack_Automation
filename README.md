# GoogleEarth_MapImport_CapMerge_TexPack_Automation
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

## This script is in the pre-release stage so issues and bugs may be present or unaccounted for - however it has had extensive testing done on it and with only one known bug is stable to use for most cases
In the Image below you can see the capture is about to take a capture from a U.S. Navy source and will cause Maps Model Importer to fail
![image](https://github.com/sir306/GoogleEarth_MapImport_CapMerge_TexPack_Automation/assets/40708936/95dfbca7-9b7d-4154-b633-3c26666fabf8)

A Link to this example has been provided:
[](url)https://earth.google.com/web/@-43.55529439,172.74939961,3.19291048a,808.72012098d,35y,156.51603316h,65.97568547t,0r
### When using this solution my only requirement is that you cite my name Nicholas Harding and cite this repository
### You also need to refer to further citations and uses from the addons creator @https://github.com/eliemichel when using his addons for your solution

