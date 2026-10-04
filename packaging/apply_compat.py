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


def patch_ib() -> None:
    fuzzy_hxx = ROOT / "ib/src/fuzzy.hxx"
    replace_once(
        fuzzy_hxx,
        """// Like a string compare, default is 75%
inline INT FuzzyCompare(const STRING &s1, const STRING& s2) {
  const int scale = 100; // 0-100 scale
  const int threshold = 75; // 75%
  int match = RatcliffCompare(s1, s2, scale);
  if (match > threshold) {
     match = 100; // Anything over threshold counts as a good match
  }
  return scale - match; // Over threshold returns 0 
}

// Compare string s1 with the first (max) len characters of str
inline INT FuzzyCompare(const STRING &s1, const UCHR *str, const size_t len) {
  return FuzzyCompare(s1, STRING(str,len)); 
}
""",
        """// Like a string compare, default is 75%
INT FuzzyCompare(const STRING &s1, const STRING& s2);

// Compare string s1 with the first (max) len characters of str
INT FuzzyCompare(const STRING &s1, const UCHR *str, const size_t len);
""",
    )

    fuzzy = ROOT / "ib/src/fuzzy.cxx"
    replace_once(
        fuzzy,
        '#include "fuzzy.hxx"\n#include <vector>\n\nextern "C" double sqrt(double x);\n',
        '#include "fuzzy.hxx"\n'
        '#include <vector>\n'
        '#include <algorithm>\n'
        '#include <cmath>\n',
    )
    replace_once(
        fuzzy,
        '#define min(x,y) ((x)>(y)?(y):(x))\n\n'
        '      int cell = min( above + 1, min(left + 1, diag + cost));',
        '      int cell = std::min(above + 1, std::min(left + 1, diag + cost));',
    )
    replace_once(
        fuzzy,
        'size_t       want = HEADROOM(need*sqrt(need),1024);',
        'size_t       want = HEADROOM(need*std::sqrt(need),1024);',
    )

    replace_once(
        fuzzy,
        "\n\n#ifdef TEST\n",
        """

INT FuzzyCompare(const STRING &s1, const STRING& s2) {
  const int scale = 100;
  const int threshold = 75;
  int match = RatcliffCompare(s1, s2, scale);
  if (match > threshold)
    match = 100;
  return scale - match;
}

INT FuzzyCompare(const STRING &s1, const UCHR *str, const size_t len) {
  return FuzzyCompare(s1, STRING(str, len));
}

#ifdef TEST
""",
    )
    # <cmath> is now included before any legacy macro definitions.
    replace_once(
        fuzzy,
        '\n#include <cmath>\n\nint RatcliffCompare',
        '\nint RatcliffCompare',
    )


    memodoc = ROOT / "ib/doctype/memodoc.cxx"
    replace_once(
        memodoc,
        '#ifdef VECTOR_INDEX\n'
        '          else if (is_encoded_embedding(Contents)) ft = FIELDTYPE::db_hnsw;\n'
        '#endif\n',
        '/* The pinned source references is_encoded_embedding() here, but no '\
        'declaration or implementation exists in ib/Schmate. Keep vector search '\
        'enabled while omitting only this broken MEMODOC auto-detection branch. */\n',
    )


    oneline_cpp = ROOT / "ib/doctype/oneline.cxx"
    replace_once(
        oneline_cpp,
        "#include <ctype.h>\n",
        "#include <ctype.h>\n#include <cstring>\n",
    )

    dfd_cpp = ROOT / "ib/src/dfd.cxx"
    replace_once(
        dfd_cpp,
        '#include "dfd.hxx"\n',
        '#include "dfd.hxx"\n#include <stdint.h>\n',
    )

    mmap_cpp = ROOT / "ib/src/mmap.cxx"
    replace_once(
        mmap_cpp,
        "#include <errno.h>\n",
        "#include <errno.h>\n#include <stdint.h>\n",
    )

    numbers = ROOT / "ib/src/numbers.cxx"
    replace_once(
        numbers,
        "#include <charconv>\n",
        "#include <charconv>\n#include <cmath>\n",
    )
    replace_once(
        numbers,
        "const NUMBER whole = floorl(x);",
        "const NUMBER whole = std::floor(x);",
    )
    replace_once(
        numbers,
        "UINT4 fract = (UINT4)floorl(f + 0.5L);",
        "UINT4 fract = (UINT4)std::floor(f + 0.5L);",
    )
    replace_once(
        numbers,
        """  /*
   * FAST PATH
   *
   * This should handle the overwhelming majority of integer metadata:
   *
   *     123
   *     -123
   *     +123
   */
  {
    INT16 value;

    const auto result = std::from_chars(p, end, value, 10);

    if (result.ec == std::errc() && result.ptr == end) {
      val   = value;
      valid = true;
      return true;
    }
  }


""",
        """  /*
   * The pinned source used std::from_chars directly with INT16 (__int128).
   * Standard libstdc++ overloads do not support __int128, so fall through to
   * the existing checked 128-bit parser below.
   */


""",
    )


    ib_cmake = ROOT / "ib/CMakeLists.txt"
    replace_once(
        ib_cmake,
        """        ibUtils
        ibLocal
        Threads::Threads
""",
        """        ibUtils
        ibLocal
        ibIO
        Threads::Threads
""",
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
    patch_ib()
    patch_bert_cpp()
    print("Applied pinned CoreQuarry packaging compatibility fixes.")


if __name__ == "__main__":
    main()
