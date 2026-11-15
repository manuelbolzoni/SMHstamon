## SMHstamon 0.3

- Fix a crash when a healthy server panel is hidden while another SMHUB server has alarms, and when a server panel is removed.
- Keep monitoring state isolated between servers, including identical host labels.
- Respect HTTP timeout, proxy and TLS settings; report failed HTTP/JSON responses without clearing existing alarms.
- Support both `unknown` and legacy `unknow` states and empty notes.
- Standardize the visible name to **SMHUB**.
- Remove **Filters**, **Actions** and **Defaults** from Settings and remove the Filters toolbar shortcut. Existing configuration values are preserved.
- Load only the SMHUB backend and remove unnecessary Kerberos dependencies.
- Repair Windows installer shortcuts and refresh the release build pipeline.

### Downloads

- `SMHstamon-0.3-win64.zip`: portable Windows x64 application; extract the entire folder and run `SMHstamon.exe`.
- `SMHstamon-0.3-win64_setup.zip`: ZIP containing the Windows x64 setup executable.
- `smhstamon_0.3_all.deb`: Debian/Ubuntu package; install with `sudo apt install ./smhstamon_0.3_all.deb`.
- `smhstamon-0.3-1.noarch.rpm`: Fedora/RPM package; install with `sudo dnf install ./smhstamon-0.3-1.noarch.rpm`.

Linux packages require Python 3 and Qt 6 dependencies supplied by the distribution. Packaging smoke tests target Ubuntu 24.04 and Fedora 43. Windows builds target Windows 10/11 x64.

Regression tests use simulated SMHUB responses; production SMHUB endpoints have not been exercised.
