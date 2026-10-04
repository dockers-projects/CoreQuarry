# Native package metadata shared by CPack generators.

set(CPACK_PACKAGE_NAME "corequarry")
set(CPACK_PACKAGE_VENDOR "CoreQuarry")
set(
    CPACK_PACKAGE_DESCRIPTION_SUMMARY
    "Local-first hybrid lexical, structural, and semantic retrieval engine"
)
set(
    CPACK_PACKAGE_HOMEPAGE_URL
    "https://github.com/dockers-projects/CoreQuarry"
)
set(CPACK_PACKAGE_CONTACT "CoreQuarry maintainers")
set(CPACK_PACKAGE_VERSION "${COREQUARRY_VERSION}")
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_SOURCE_DIR}/LICENSE")

# CPack stages packages as a normal system installation. The archive generator
# therefore contains usr/bin, usr/lib/ib, ... and can be relocated as a whole
# by Homebrew or extracted under / by users who choose the portable tarball.
set(CPACK_PACKAGING_INSTALL_PREFIX "/usr")

# Keep portable archive names deterministic across CI runners.
set(
    CPACK_PACKAGE_FILE_NAME
    "corequarry-${COREQUARRY_VERSION}-${CMAKE_SYSTEM_NAME}-${COREQUARRY_PACKAGE_ARCH}"
)

# Debian/Ubuntu.
set(CPACK_DEBIAN_FILE_NAME DEB-DEFAULT)
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "CoreQuarry maintainers")
set(CPACK_DEBIAN_PACKAGE_SECTION "utils")
set(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
set(CPACK_DEBIAN_PACKAGE_SHLIBDEPS ON)

# Fedora/RHEL-family.
set(CPACK_RPM_FILE_NAME RPM-DEFAULT)
set(CPACK_RPM_PACKAGE_LICENSE "Apache-2.0")
set(CPACK_RPM_PACKAGE_GROUP "Applications/System")
set(CPACK_RPM_PACKAGE_AUTOREQPROV ON)

if(APPLE)
    set(CPACK_GENERATOR "TGZ")
elseif(UNIX)
    set(CPACK_GENERATOR "TGZ;DEB;RPM")
endif()

include(CPack)
