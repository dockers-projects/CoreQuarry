# Packaging and releases

CoreQuarry packages are produced from the repository's pinned submodules. The
release pipeline does not fetch newer dependency revisions while packaging, so
the package corresponds to the exact source graph recorded by the release tag.

## Supported package outputs

| Platform | Architectures | Output | Install path |
| --- | --- | --- | --- |
| Debian / Ubuntu | amd64, arm64 | `.deb` + `.tar.gz` | `/usr/bin`, `/usr/lib/ib` |
| Fedora / RHEL family | x86_64, aarch64 | `.rpm` | `/usr/bin`, `/usr/lib/ib` |
| macOS | Apple Silicon, Intel | `.tar.gz` + generated Homebrew formula | Homebrew Cellar or relocated archive |
| Windows | — | not native yet | see Windows section |

The GGUF model files are intentionally not embedded in the OS packages. Model
storage remains separate from the program package.

## Linux installation

Download the matching asset from a GitHub Release.

Debian / Ubuntu:

```bash
sudo apt install ./corequarry_<version>_<arch>.deb
quarry --help
```

Fedora / RHEL-family:

```bash
sudo dnf install ./corequarry-<version>-1.<arch>.rpm
quarry --help
```

The portable Linux archive contains an install tree rooted at `usr/`. It can
be inspected or relocated without installing the DEB/RPM.

## macOS installation

Each tagged release contains archives for both supported Mac architectures:

```text
corequarry-<version>-Darwin-arm64.tar.gz
corequarry-<version>-Darwin-x86_64.tar.gz
```

The release also contains a generated `corequarry.rb` whose SHA-256 values
match those exact archives. Until a dedicated Homebrew tap repository is
published, install the release formula locally:

```bash
curl -LO https://github.com/dockers-projects/CoreQuarry/releases/download/v<version>/corequarry.rb
brew install ./corequarry.rb
```

The formula declares the external libraries used by the prebuilt CoreQuarry
binary and relocates the packaged `usr/` tree into the Homebrew Cellar.

A dedicated tap can consume the same generated formula later without changing
the CoreQuarry build or package format.

## Windows status

The current CoreQuarry workspace cannot produce a native Windows package yet.
The pinned `ib` CMake project explicitly accepts macOS, Linux/Unix, and BSD
and stops configuration on other systems. That is a source portability issue,
not merely an installer issue, so creating an MSI or WinGet manifest now would
publish an artifact that cannot work.

Windows users can currently use the Debian package inside an Ubuntu WSL
environment. Native Windows delivery requires making `ib` and the linked
dependencies build successfully on Windows first; after that the same release
pipeline can add a ZIP/MSI and WinGet manifest.

## Release process

The `Native packages` GitHub Actions workflow runs on pull requests affecting
packaging, can be run manually, and publishes release assets for tags matching
`v*`.

For a release:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The tag build:

1. checks out all pinned submodules recursively;
2. builds DEB packages on Ubuntu amd64 and arm64;
3. builds RPM packages inside Fedora x86_64 and aarch64 environments;
4. builds macOS archives on Apple Silicon and Intel runners;
5. installs the generated Linux packages in clean distro containers;
6. smoke-tests the packaged macOS install tree with `quarry --help`;
7. renders the versioned Homebrew formula from the two macOS archives;
8. generates `SHA256SUMS`;
9. publishes all artifacts to the GitHub Release.

Manual workflow runs build and test packages but do not publish a GitHub
Release.

## Package contents

The workspace adds the main `quarry` executable to the install tree because
the pinned `ib` install rules currently install the supporting tools and
libraries but omit `quarry`.

The Schmate shared runtime used by vector search is installed into
`lib/ib`, alongside the ib shared libraries. The existing relative runtime
search path used by `quarry` therefore remains valid after packaging:

- Linux: `$ORIGIN/../lib/ib`
- macOS: `@loader_path/../lib/ib`

External system libraries remain normal package/Homebrew dependencies rather
than being copied into the CoreQuarry package.
