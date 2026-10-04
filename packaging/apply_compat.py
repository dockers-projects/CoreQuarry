#!/usr/bin/env python3
"""Apply narrowly-scoped compatibility fixes to pinned CoreQuarry submodules.

This script is intentionally strict: every replacement must match the exact
pinned source text. If a submodule is updated, packaging fails instead of
silently applying a stale compatibility edit.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{path.relative_to(ROOT)}: expected exactly one compatibility "
            f"anchor, found {count}"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def add_include(path: str, anchor: str, include: str) -> None:
    target = ROOT / path
    replace_once(target, anchor, anchor + include)


def patch_schmate() -> None:
    add_include(
        "Schmate/include/Logger.hpp",
        "#include <iostream>\n",
        "#include <atomic>\n#include <cstring>\n",
    )
    add_include(
        "Schmate/include/FileLock.hpp",
        "#include <sys/file.h>\n",
        "#include <functional>\n",
    )
    add_include(
        "Schmate/include/hnswlib/hnswalg.h",
        "#include <memory>\n",
        "#include <functional>\n",
    )
    add_include(
        "Schmate/include/unified_hnsw.hpp",
        "#include <queue>\n",
        "#include <functional>\n",
    )

    quantized = ROOT / "Schmate/include/hnswlib/quantized.h"
    replace_once(
        quantized,
        '#include "int_storage.h"\n#include "hnswlib.h"\n',
        '#include "int_storage.h"\n'
        "\n"
        "namespace hnswlib {\n"
        "inline float compute_dist_L2_pass(\n"
        "    int bits, const uint8_t* a, const uint8_t* b, size_t dim);\n"
        "}\n"
        "\n"
        '#include "hnswlib.h"\n',
    )

    logger_cpp = ROOT / "Schmate/src/Logger.cpp"
    replace_once(
        logger_cpp,
        "openlog(prefix_, LOG_PID | LOG_CONS, LOG_USER);",
        "openlog(prefix_.c_str(), LOG_PID | LOG_CONS, LOG_USER);",
    )
    replace_once(
        logger_cpp,
        "file_stream.open(filename, std::ios::app);",
        "file_stream.open(std::string(filename), std::ios::app);",
    )

    bert_index = ROOT / "Schmate/src/BertIndex.cpp"
    replace_once(
        bert_index,
        "#include <signal.h>\n",
        "#include <signal.h>\n"
        "#if !defined(_MSDOS) && !defined(_WIN32)\n"
        "#include <sys/wait.h>\n"
        "#endif\n",
    )


def patch_bert_cpp() -> None:
    cmake = ROOT / "bert.cpp/CMakeLists.txt"
    replace_once(
        cmake,
        """if (GGML_METAL)
    add_compile_definitions(GGML_USE_METAL)

    # copy ggml-metal.metal to bin directory

    configure_file(ggml/src/ggml-metal.metal ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/ggml-metal.metal COPYONLY)

endif()
""",
        """if (GGML_METAL)
    add_compile_definitions(GGML_USE_METAL)

    # Older ggml revisions shipped one monolithic ggml-metal.metal file.
    # Current ggml organizes/embeds Metal kernels differently.
    if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/ggml/src/ggml-metal.metal")
        configure_file(
            ggml/src/ggml-metal.metal
            ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/ggml-metal.metal
            COPYONLY
        )
    endif()

endif()
""",
    )


def main() -> None:
    patch_schmate()
    patch_bert_cpp()
    print("Applied pinned CoreQuarry packaging compatibility fixes.")


if __name__ == "__main__":
    main()
