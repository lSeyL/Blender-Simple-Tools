"""Build the Blender installer without Python caches or development files."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent


def build():
    output = ROOT / 'install' / 'simple_tools.zip'
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for source in sorted((ROOT / 'simple_tools').glob('*.py')):
            archive.write(source, f'simple_tools/{source.name}')
        archive.write(ROOT / 'README.md', 'simple_tools/README.md')
    with ZipFile(output) as archive:
        assert archive.testzip() is None
    print(f'Built {output}')


if __name__ == '__main__':
    build()
