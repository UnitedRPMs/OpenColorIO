%if ! 0%{?bootstrap}
%global docs 1
%global tests 1
%endif

Name:           OpenColorIO
Version:        1.1.1
Release:        11%{?dist}
Summary:        Enables color transforms and image display across graphics apps

License:        BSD
URL:            http://opencolorio.org/
Source0:        https://github.com/imageworks/OpenColorIO/archive/v%{version}/%{name}-%{version}.tar.gz

# Work with system libraries instead of bundled.
Patch0:         OpenColorIO-setuptools.patch
# Fix build against yaml-cpp 0.6.0+
# This patch is fine for our case (building against system yaml-cpp)
# but probably a bit too simple-minded to upstream as-is. See
# https://github.com/imageworks/OpenColorIO/issues/517
Patch1:         ocio-1.1.0-yamlcpp060.patch
Patch2:         ocio-glext_h.patch
Patch3:	8d48ee8da42de2d878db7b42586db8b3c67f83e1.patch

# Utilities
BuildRequires:  cmake gcc-c++
BuildRequires:  help2man
BuildRequires:  python3-markupsafe
BuildRequires:  python3-setuptools

# Libraries
BuildRequires:  boost-devel
BuildRequires:  mesa-libGL-devel mesa-libGLU-devel
BuildRequires:  libX11-devel libXmu-devel libXi-devel
BuildRequires:  freeglut-devel
BuildRequires:  glew-devel
BuildRequires:  python3-devel
BuildRequires:  zlib-devel
BuildRequires:  OpenEXR-devel

# WARNING: OpenColorIO and OpenImageIO are cross dependent. 
# If an ABI incompatible update is done in one, the other also needs to be
# rebuilt.
# Answer// Sure but not a build dependency using both packages ¿How do you solve the lop?) ...
# BuildRequires:  OpenImageIO-devel >= 2.0.10


#######################
# Unbundled libraries #
#######################
BuildRequires:  tinyxml-devel
BuildRequires:  lcms2-devel
#BuildRequires:  yaml-cpp-devel >= 0.5.0
BuildRequires:	git

%if 0%{?docs}
# Needed for pdf documentation generation
BuildRequires:  texlive-latex-bin-bin texlive-gsftopk-bin texlive-dvips
# Fonts
BuildRequires:  texlive-cm texlive-ec texlive-times texlive-helvetic
BuildRequires:  texlive-courier
# Map tables
BuildRequires:  texlive-cmap
# Font maps
BuildRequires:  texlive-updmap-map
# Babel
BuildRequires:  texlive-babel-english
# Styles
BuildRequires:  texlive-fancyhdr texlive-fancybox texlive-mdwtools
BuildRequires:  texlive-parskip texlive-multirow texlive-titlesec
BuildRequires:  texlive-framed texlive-threeparttable texlive-wrapfig
# Other
BuildRequires:  texlive-hyphen-base
%endif


# The following bundled projects are only used for document generation.
#BuildRequires:  python-docutils
#BuildRequires:  python-jinja2
#BuildRequires:  python-pygments
#BuildRequires:  python-setuptools
#BuildRequires:  python-sphinx

%if ! 0%{?docs}
# upgrade path for when/if docs are not included
Obsoletes: %{name}-doc < %{version}-%{release}
%endif


%description
OCIO enables color transforms and image display to be handled in a consistent
manner across multiple graphics applications. Unlike other color management
solutions, OCIO is geared towards motion-picture post production, with an
emphasis on visual effects and animation color pipelines.


%package tools
Summary:        Command line tools for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description tools
Command line tools for %{name}.


%package doc
BuildArch:      noarch
Summary:        API Documentation for %{name}
Requires:       %{name} = %{version}-%{release}

%description doc
API documentation for %{name}.


%package devel
Summary:        Development libraries and headers for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Development libraries and headers for %{name}.


%prep
%autosetup -p1

# Remove what bundled libraries
rm -f ext/lcms*
rm -f ext/tinyxml*
# rm -f ext/yaml*

sed -i "s/-Werror//g" src/core/CMakeLists.txt
sed -i "s/-Werror//g" src/pyglue/CMakeLists.txt
sed -i "s/push(hidden)/push(default)/g" src/core/OCIOYaml.cpp


%build

# Change shebang in all relevant files in this directory and all subdirectories
# See `man find` for how the `-exec command {} +` syntax works
find -type f -exec sed -iE '1s=^#! */usr/bin/\(python\|env python\)[23]\?=#!%{__python3}=' {} +

rm -rf build && mkdir build && pushd build
%cmake \
       -DCMAKE_VERBOSE_MAKEFILE:BOOL=OFF \
       -DOCIO_BUILD_STATIC=OFF \
       -DOCIO_BUILD_DOCS=%{?docs:ON}%{?!docs:OFF} \
       -DOCIO_BUILD_PYGLUE=OFF \
       -DOCIO_BUILD_TESTS=%{?tests:ON}%{?!tests:OFF} \
       -DPYTHON=%{__python3} \
       -DUSE_EXTERNAL_YAML=OFF \
       -DUSE_EXTERNAL_TINYXML=TRUE \
       -DUSE_EXTERNAL_LCMS=TRUE \
       -DUSE_EXTERNAL_SETUPTOOLS=TRUE \
%ifnarch x86_64
       -DOCIO_USE_SSE=OFF \
%endif
       -DOpenGL_GL_PREFERENCE=GLVND \
       ../

%make_build


%install
pushd build
%make_install

# Generate man pages
mkdir -p %{buildroot}%{_mandir}/man1
help2man -N -s 1 %{?fedora:--version-string=%{version}} \
         -o %{buildroot}%{_mandir}/man1/ociocheck.1 \
         src/apps/ociocheck/ociocheck
help2man -N -s 1 %{?fedora:--version-string=%{version}} \
         -o %{buildroot}%{_mandir}/man1/ociobakelut.1 \
         src/apps/ociobakelut/ociobakelut
popd

%if 0%{?docs}
# Move installed documentation back so it doesn't conflict with the main package
mkdir _tmpdoc
mv %{buildroot}%{_docdir}/%{name}/* _tmpdoc/
%endif

# Fix location of cmake files.
mkdir -p %{buildroot}%{_datadir}/cmake/Modules
find %{buildroot} -name "*.cmake" -exec mv {} %{buildroot}%{_datadir}/cmake/Modules/ \;


%check
# Testing passes locally in mock but fails on the fedora build servers.
#pushd build && make test


%ldconfig_scriptlets


%files
%license LICENSE
%doc ChangeLog README.md
%{_libdir}/*.so.*
%dir %{_datadir}/ocio
%{_datadir}/ocio/setup_ocio.sh
#{python3_sitearch}/*.so

%files tools
%{_bindir}/*
%{_mandir}/man1/*

%if 0%{?docs}
%files doc
%doc _tmpdoc/*
%endif

%files devel
%{_datadir}/cmake/Modules/*
%{_includedir}/OpenColorIO/
#{_includedir}/PyOpenColorIO/
%{_libdir}/*.so
%{_libdir}/pkgconfig/%{name}.pc


%changelog

* Mon Oct 05 2020 Unitedrpms Project <unitedrpms AT protonmail DOT com> 1.1.1-11
- Rebuilt

* Sun May 31 2020 Unitedrpms Project <unitedrpms AT protonmail DOT com> 1.1.1-9
- Rebuilt for python3.9

* Tue Nov 19 2019 Unitedrpms Project <unitedrpms AT protonmail DOT com> 1.1.1-8
- Rebuilt 

* Thu Sep 05 2019 David Va <davidva AT tuta DOT io> - 1.1.1-7
- Upstream

* Wed Jul 24 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Wed Apr 03 2019 Richard Shaw <hobbes1069@gmail.com> - 1.1.1-1
- Update to 1.1.1.
- Removing python glue module as python 3 is not currently supported.

* Thu Jan 31 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.0-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Thu Dec 13 2018 Richard Shaw <hobbes1069@gmail.com> - 1.1.0-10
- Add patch for OIIO 2.0 and mesa glext.h header changes.

* Mon Sep 24 2018 Richard Shaw <hobbes1069@gmail.com> - 1.1.0-9
- Obsolete Python2 library and build Python3 library.

* Thu Aug 23 2018 Nicolas Chauvet <kwizart@gmail.com> - 1.1.0-8
- Rebuilt for glew 2.1.0

* Thu Jul 12 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Thu Feb 22 2018 Adam Williamson <awilliam@redhat.com> - 1.1.0-6
- Rebuild with bootstrap disabled, so we get docs again

* Thu Feb 22 2018 Peter Robinson <pbrobinson@fedoraproject.org> 1.1.0-5
- Rebuild

* Tue Feb 20 2018 Rex Dieter <rdieter@fedoraproject.org> - 1.1.0-4
- support %%bootstrap (no docs, no tests)
- enable bootstrap mode on f28+ to workaround bug #1546964

* Mon Feb 19 2018 Adam Williamson <awilliam@redhat.com> - 1.1.0-3
- Fix build with yaml-cpp 0.6+ (patch out bogus hidden visibility)
- Fix build with GCC 8 (issues in Python bindings, upstream PR #518)
- Rebuild for yaml-cpp 0.6.1

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Jan 12 2018 Richard Shaw <hobbes1069@gmail.com> - 1.1.0-1
- Update to latest upstream release.

* Sun Jan 07 2018 Richard Shaw <hobbes1069@gmail.com> - 1.0.9-20
- Rebuild for OpenImageIO 1.8.7.

* Wed Dec 06 2017 Richard Shaw <hobbes1069@gmail.com> - 1.0.9-19
- Fix ambiguous Python 2 dependency declarations
  https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.9-18
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.9-17
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jul 07 2017 Igor Gnatenko <ignatenko@redhat.com> - 1.0.9-16
- Rebuild due to bug in RPM (RHBZ #1468476)

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.9-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Jan 10 2017 Orion Poplawski <orion@cora.nwra.com> - 1.0.9-14
- Rebuild for glew 2.0.0

* Mon Oct 03 2016 Richard Shaw <hobbes1069@gmail.com> - 1.0.9-13
- Rebuild for new OpenImageIO.

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.9-12
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.9-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jan 14 2016 Richard Shaw <hobbes1069@gmail.com> - 1.0.9-10
- Rebuild for OpenImageIO 1.6.9.

* Thu Jan 14 2016 Adam Jackson <ajax@redhat.com> - 1.0.9-9
- Rebuild for glew 1.13

* Tue Jun 16 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.9-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 1.0.9-7
- Rebuilt for GCC 5 C++11 ABI change

* Wed Jan 28 2015 Richard Shaw <hobbes1069@gmail.com> - 1.0.9-6
- Rebuild for OpenImageIO 1.5.11.

* Fri Aug 15 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.9-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Jun 06 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.9-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed May 21 2014 Richard Shaw <hobbes1069@gmail.com> - 1.0.9-3
- Rebuild for updated OpenImageIO 1.4.7.

* Mon Jan 13 2014 Richard Shaw <hobbes1069@gmail.com> - 1.0.9-2
- Add OpenImageIO as build requirement to build additional command line tools.
  Fixes BZ#1038860.

* Wed Nov  6 2013 Richard Shaw <hobbes1069@gmail.com> - 1.0.9-1
- Update to latest upstream release.

* Mon Sep 23 2013 Richard Shaw <hobbes1069@gmail.com> - 1.0.8-6
- Rebuild against yaml-cpp03 compatibility package.

* Mon Aug 26 2013 Richard Shaw <hobbes1069@gmail.com> - 1.0.8-5
- Fix for new F20 feature, unversion doc dir. Fixes BZ#1001264

* Fri Aug 02 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Dec 11 2012 Richard Shaw <hobbes1069@gmail.com> - 1.0.8-1
- Update to latest upstream release.

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.7-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Apr 26 2012 Richard Shaw <hobbes1069@gmail.com> - 1.0.7-4
- Only use SSE instructions on x86_64.

* Wed Apr 25 2012 Richard Shaw <hobbes1069@gmail.com> - 1.0.7-3
- Misc spec cleanup for packaging guidelines.
- Disable testing for now since it fails on the build servers.

* Wed Apr 18 2012 Richard Shaw <hobbes1069@gmail.com> - 1.0.7-1
- Latest upstream release.

* Thu Apr 05 2012 Richard Shaw <hobbes1069@gmail.com> - 1.0.6-1
- Latest upstream release.

* Wed Nov 16 2011 Richard Shaw <hobbes1069@gmail.com> - 1.0.2-1
- Initial release.
