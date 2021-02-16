from pathlib import Path
import shutil

def copy_directory_content(src:Path, dest:Path):
  for item in src.iterdir():
    if (item.is_dir()):
      shutil.copytree(item, dest)
    else:
      shutil.copy2(item, dest)
