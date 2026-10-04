cmake_minimum_required(VERSION 3.20)
project(CoreQuarryWorkspace)

include(GNUInstallDirs)

set(
    COREQUARRY_VERSION
    "0.0.0"
    CACHE STRING
    "Version embedded into CoreQuarry packages"
)

set(
    COREQUARRY_PACKAGE_ARCH
    "${CMAKE_SYSTEM_PROCESSOR}"
    CACHE STRING
    "Architecture label used in portable package file names"
)

# ==============================================================================
# Hardware Acceleration & Optimization Flags
# ==============================================================================

# Keep workspace-wide optimization portable. Individual subprojects may add
# stronger target-specific flags of their own.
add_compile_options(
    $<$<COMPILE_LANG_AND_ID:C,GNU,Clang,AppleClang>:-O3>
    $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-O3>
)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(APPLE)
    # Force entire build tree to use Apple Silicon acceleration.
    add_compile_definitions(
        GGML_USE_METAL=1
        GGML_USE_ACCELERATE=1
    )
endif()

if(CMAKE_CUDA_COMPILER OR DEFINED CUDAToolkit_FOUND)
    # Force entire build tree to use NVIDIA CUDA acceleration.
    add_compile_definitions(
        GGML_USE_CUDA=1
    )
endif()

# ==============================================================================
# Dependency Resolution
# ==============================================================================

# Define the expected path to GGML at project root.
set(GGML_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/ggml")

if(EXISTS "${GGML_SOURCE_DIR}/CMakeLists.txt")
    message(STATUS "Found GGML at base directory: ${GGML_SOURCE_DIR}")

    # GGML will now successfully inherit METAL, ACCELERATE, CUDA, and
    # workspace-wide optimization/PIC settings.
    add_subdirectory(
        "${GGML_SOURCE_DIR}"
        "${CMAKE_CURRENT_BINARY_DIR}/ggml"
        EXCLUDE_FROM_ALL
    )
else()
    message(FATAL_ERROR
        "GGML not found at ${GGML_SOURCE_DIR}. "
        "Please clone CoreQuarry with --recurse-submodules."
    )
endif()

# Add Schmate first so its targets (sbert_extended, bert_model) are defined.
add_subdirectory(Schmate)

# Schmate currently carries a Darwin-only linker option on these targets
# unconditionally. Remove exactly that option for non-Apple package builds so
# GNU/LLVM linkers on Linux do not receive '-undefined dynamic_lookup'.
if(NOT APPLE)
    foreach(_schmate_target sbert_shared sbert_extended)
        if(TARGET "${_schmate_target}")
            get_target_property(
                _schmate_link_options
                "${_schmate_target}"
                LINK_OPTIONS
            )
            if(_schmate_link_options)
                list(
                    FILTER
                    _schmate_link_options
                    EXCLUDE
                    REGEX "^-Wl,-undefined,dynamic_lookup$"
                )
                set_property(
                    TARGET "${_schmate_target}"
                    PROPERTY LINK_OPTIONS "${_schmate_link_options}"
                )
            endif()
        endif()
    endforeach()
endif()

add_subdirectory(ib)

# ==============================================================================
# Install tree used by native packages
# ==============================================================================

# ib installs its libraries and helper CLIs, but the pinned revision does not
# install the main CoreQuarry entry point. Install it from the workspace.
install(
    TARGETS quarry
    RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
)

# quarry links to Schmate when vector support is enabled. Keep the shared
# Schmate runtime next to the ib shared libraries so quarry's relative RPATH
# ($ORIGIN/../lib/ib or @loader_path/../lib/ib) resolves after installation.
install(
    TARGETS sbert_extended
    ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}/ib"
    LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}/ib"
    RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
)

install(
    FILES
        README.md
        LICENSE
        NOTICE
    DESTINATION "${CMAKE_INSTALL_DATADIR}/doc/corequarry"
)

include(cmake/Packaging.cmake)
