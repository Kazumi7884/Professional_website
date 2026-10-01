from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from build import ROOT, build

PUBLIC_EXCLUSIONS = {'build-info.json'}


def create_archive(destination=ROOT / 'deploy/successor-upload.zip'):
    build()
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, 'w', ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / 'build').rglob('*')):
            if path.is_file() and path.relative_to(ROOT / 'build').as_posix() not in PUBLIC_EXCLUSIONS:
                archive.write(path, path.relative_to(ROOT / 'build'))
    return destination


if __name__ == '__main__':
    destination = create_archive()
    print(destination)

