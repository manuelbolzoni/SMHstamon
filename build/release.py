"""Build SMHstamon release packages using native packaging tools."""
import argparse
import ast
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def version():
    tree = ast.parse((ROOT / 'Nagstamon/Config.py').read_text(encoding='utf-8'))
    app = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AppInfo')
    return next(ast.literal_eval(n.value) for n in app.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in n.targets))


def run(*args):
    subprocess.run([str(a) for a in args], check=True, cwd=ROOT)


def windows(output, ver, iscc):
    with tempfile.TemporaryDirectory(prefix='smhstamon-build-') as temp:
        temp = Path(temp)
        run(sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir',
            '--contents-directory', '.', '--windowed', '--name', 'SMHstamon',
            '--distpath', temp / 'dist', '--workpath', temp / 'work', '--specpath', temp,
            '--add-data', str(ROOT / 'Nagstamon/resources') + ';resources',
            '--icon', ROOT / 'Nagstamon/resources/smhstamon.ico',
            '--hidden-import', 'PyQt6.QtSvg', '--hidden-import', 'PyQt6.QtMultimedia',
            ROOT / 'smhstamon.py')
        bundle = temp / 'dist/SMHstamon'
        assert (bundle / 'SMHstamon.exe').is_file()
        assert (bundle / 'resources/qui/settings_main.ui').is_file()
        shutil.copy2(ROOT / 'LICENSE', bundle / 'LICENSE.txt')
        run(iscc, '/Dsource=' + str(bundle), '/Dversion_is=' + ver,
            '/Dversion=' + ver, '/Darch=64', '/Darchs_allowed=x64',
            '/Dresources=' + str(bundle / 'resources'), '/O' + str(output),
            ROOT / 'build/windows/nagstamon.iss')
        shutil.make_archive(str(output / f'SMHstamon-{ver}-win64'), 'zip',
                            root_dir=bundle.parent, base_dir=bundle.name)
        setup = output / f'SMHstamon-{ver}-win64_setup.exe'
        assert setup.is_file()
        with zipfile.ZipFile(output / f'SMHstamon-{ver}-win64_setup.zip', 'w',
                             zipfile.ZIP_DEFLATED) as archive:
            archive.write(setup, setup.name)
        setup.unlink()  # The requested setup asset is a ZIP containing the EXE.


def stage_linux(root):
    app = root / 'usr/lib/smhstamon'
    app.mkdir(parents=True)
    shutil.copytree(ROOT / 'Nagstamon', app / 'Nagstamon',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy2(ROOT / 'smhstamon.py', app / 'smhstamon.py')
    launcher = root / 'usr/bin/smhstamon'
    launcher.parent.mkdir(parents=True)
    launcher.write_text('#!/usr/bin/python3\nimport runpy, sys\nsys.path.insert(0, "/usr/lib/smhstamon")\nrunpy.run_path("/usr/lib/smhstamon/smhstamon.py", run_name="__main__")\n')
    launcher.chmod(0o755)
    desktop = root / 'usr/share/applications/smhstamon.desktop'
    desktop.parent.mkdir(parents=True)
    desktop.write_text('[Desktop Entry]\nType=Application\nName=SMHstamon\nComment=SMHUB status monitor\nExec=smhstamon\nIcon=smhstamon\nTerminal=false\nCategories=Network;Monitor;\n')
    icons = root / 'usr/share/pixmaps'
    icons.mkdir(parents=True)
    shutil.copy2(ROOT / 'Nagstamon/resources/smhstamon.svg', icons / 'smhstamon.svg')
    docs = root / 'usr/share/doc/smhstamon'
    docs.mkdir(parents=True)
    for name in ('LICENSE', 'COPYRIGHT', 'README.md'):
        shutil.copy2(ROOT / name, docs / name)


def linux(output, ver):
    with tempfile.TemporaryDirectory(prefix='smhstamon-build-') as temp:
        temp = Path(temp)
        stage = temp / 'stage'
        stage_linux(stage)
        debroot = temp / 'deb'
        shutil.copytree(stage, debroot)
        control = debroot / 'DEBIAN/control'
        control.parent.mkdir()
        control.write_text(f'''Package: smhstamon
Version: {ver}
Section: net
Priority: optional
Architecture: all
Maintainer: Manuel Bolzoni <manuel.bolzoni@alveo.it>
Depends: python3, python3-bs4, python3-dateutil, python3-keyring, python3-lxml, python3-psutil, python3-pyqt6, python3-pyqt6.qtsvg, python3-pyqt6.qtmultimedia, python3-requests, python3-socks
Homepage: https://github.com/manuelbolzoni/SMHstamon
Description: SMHUB status monitor for your desktop
 Monitor multiple SMHUB JSON API endpoints from the system tray or desktop.
''')
        deb = output / f'smhstamon_{ver}_all.deb'
        run('dpkg-deb', '--root-owner-group', '--build', debroot, deb)
        run('dpkg-deb', '--info', deb)
        top = temp / 'rpm'
        for folder in ('BUILD', 'BUILDROOT', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS'):
            (top / folder).mkdir(parents=True)
        spec = top / 'SPECS/smhstamon.spec'
        spec.write_text(f'''Name: smhstamon
Version: {ver}
Release: 1
Summary: SMHUB status monitor for your desktop
License: GPL-2.0-or-later
URL: https://github.com/manuelbolzoni/SMHstamon
BuildArch: noarch
AutoReqProv: no
Requires: python3, python3-beautifulsoup4, python3-dateutil, python3-keyring, python3-lxml, python3-psutil, python3-qt6, python3-requests, python3-pysocks

%description
Monitor multiple SMHUB JSON API endpoints from the system tray or desktop.

%prep
%build
%install
mkdir -p %{{buildroot}}
cp -a "{stage}/usr" %{{buildroot}}/

%files
/usr/bin/smhstamon
/usr/lib/smhstamon
/usr/share/applications/smhstamon.desktop
/usr/share/pixmaps/smhstamon.svg
%doc /usr/share/doc/smhstamon
''')
        run('rpmbuild', '--define', '_topdir ' + str(top), '--define',
            '_build_id_links none', '-bb', spec)
        packages = list((top / 'RPMS/noarch').glob('*.rpm'))
        assert len(packages) == 1
        shutil.copy2(packages[0], output / packages[0].name)
        run('rpm', '-qip', output / packages[0].name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('platform', choices=('windows', 'linux'))
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/release')
    parser.add_argument('--iscc', default='iscc')
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.platform == 'windows':
        windows(args.output, version(), args.iscc)
    else:
        linux(args.output, version())
