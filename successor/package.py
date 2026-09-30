from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from build import ROOT, build

if __name__ == '__main__':
    build()
    destination = ROOT / 'deploy/successor-upload.zip'
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, 'w', ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / 'build').rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT / 'build'))
    print(destination)
