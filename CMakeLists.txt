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

option(
    COREQUARRY_PORTABLE_BUILD
    "Build distributable binaries without CI-host-specific CPU tuning"
    OFF
)

if(COREQUARRY_PORTABLE_BUILD)
    # Release packages must run on a broad CPU baseline rather than inheriting
    # the instruction set of the hosted runner that happened to build them.
    set(GGML_NATIVE OFF CACHE BOOL "Disable host-specific ggml tuning" FORCE)
    set(GGML_AVX OFF CACHE BOOL "Disable AVX in portable packages" FORCE)
    set(GGML_AVX2 OFF CACHE BOOL "Disable AVX2 in portable packages" FORCE)
    set(GGML_FMA OFF CACHE BOOL "Disable FMA in portable packages" FORCE)

    # The pinned Schmate HNSW fork currently contains an incomplete manual-SIMD
    # branch. Use its scalar/portable implementation for distributable builds;
    # developer/source builds remain unchanged unless this option is enabled.
    add_compile_definitions(NO_MANUAL_VECTORIZATION)
endif()

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

# quarry links transitively through Schmate -> bert -> ggml. Keep every
# project-owned shared runtime in the same private directory so packages do not
# depend on build-tree paths. Optional ggml backends are installed only when
# their targets exist on the current platform.
set(
    _corequarry_runtime_targets
    sbert_extended
    bert
    ggml
    ggml-base
    ggml-cpu
    ggml-blas
    ggml-metal
)

foreach(_runtime_target IN LISTS _corequarry_runtime_targets)
    if(TARGET "${_runtime_target}")
        if(APPLE)
            set_property(
                TARGET "${_runtime_target}"
                APPEND PROPERTY INSTALL_RPATH "@loader_path"
            )
        elseif(UNIX)
            set_property(
                TARGET "${_runtime_target}"
                APPEND PROPERTY INSTALL_RPATH "$ORIGIN"
            )
        endif()

        install(
            TARGETS "${_runtime_target}"
            ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}/ib"
            LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}/ib"
            RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
        )
    endif()
endforeach()

install(
    FILES
        README.md
        LICENSE
        NOTICE
    DESTINATION "${CMAKE_INSTALL_DATADIR}/doc/corequarry"
)

include(cmake/Packaging.cmake)
