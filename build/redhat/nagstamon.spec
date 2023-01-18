%global gitdate <null>
%global commit <null>
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:     smhstamon
Version:  0.1
Release:  0.1.%{gitdate}git%{shortcommit}%{?dist}
Summary:  SMHUB status monitor for desktop

License:  GPLv2+
URL:      https://smhub.retelit.it
Source0:  https://github.com/manuelbolzoni/SMHstamon/archive/%{commit}/nagstamon-%{commit}.tar.gz

BuildArch:     noarch
BuildRequires: python3-devel
BuildRequires: python3-qt5-devel
BuildRequires: desktop-file-utils
Requires:      python3
Requires:      python3-beautifulsoup4
Requires:      python3-crypto
Requires:      python3-cryptography
Requires:      python3-dateutil
Requires:      python3-dbus
Requires:      python3-keyring
Requires:      python3-lxml
Requires:      python3-psutil
Requires:      python3-pysocks
Requires:      python3-qt5
Requires:      python3-requests
Requires:      python3-requests-kerberos
Requires:      python3-SecretStorage
Requires:      qt5-qtsvg
Requires:      qt5-qtmultimedia

%description
SMHstamon is a SMHUB status monitor which takes place in system tray
or on desktop (GNOME, KDE, Windows) as floating status bar to inform
you in real-time about the status of your SMHUB interface.

%prep
%setup -qn Nagstamon-%{commit}

%build
%{__python3} setup.py build

%install
%{__python3} setup.py install --single-version-externally-managed -O1 --root=%{buildroot}

#Provide directory to install icon for desktop file
mkdir -p %{buildroot}%{_datadir}/pixmaps

#Copy icon to pixmaps directory
cp Nagstamon/resources/%{name}.svg %{buildroot}%{_datadir}/pixmaps/%{name}.svg

#Remove execute bit from icon
chmod -x %{buildroot}%{_datadir}/pixmaps/%{name}.svg

#Remove the file extension for convenience
mv %{buildroot}%{_bindir}/%{name}.py %{buildroot}%{_bindir}/%{name}

desktop-file-install --dir %{buildroot}/%{_datadir}/applications\
                     --delete-original\
                     --set-icon=%{name}.svg\
                     %{buildroot}%{python3_sitelib}/Nagstamon/resources/%{name}.desktop

%files
%doc ChangeLog
%license COPYRIGHT LICENSE
%{_datadir}/pixmaps/%{name}.svg
%{_datadir}/applications/%{name}.desktop
%{python3_sitelib}/Nagstamon/
%{_bindir}/%{name}
%{_mandir}/man1/%{name}.1*
%{python3_sitelib}/%{name}*.egg-info

%changelog
* Manuel Bolzoni <manuel.bolzoni@retelit.it> Mon 16 Jan 2023 22:00:00 +0100
- Initial .spec file
