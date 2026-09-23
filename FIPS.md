# ICU4C fips module

This fork exports `icu` from `fips-files/icu`. Upstream sources and the original
Autotools / Visual Studio projects remain unchanged.

## Import and link

```yaml
imports:
    fips-icu:
        git: https://github.com/kochol/fips-icu.git
```

The application initializes fips once in its root, as described in the
[fips CMake guide](https://floooh.github.io/fips/docs/cmakeguide/).
Use `fips_deps(icu)` inside `fips_begin_app` / `fips_end_app`.
For manual imports, call `fips_import_fips_icu_icu()` first.

The umbrella target links `icui18n`, `icuuc` and `icudata`. Aliases:
`ICU::i18n`, `ICU::uc`, `ICU::data`. For only bidi/break services, link `icuuc`.
Headers, C++17 and `U_STATIC_IMPLEMENTATION` propagate to consumers.

Static libraries use `fips_begin_lib` / `fips_end_lib` when imported by fips.
Plain CMake fallback is available for independent tests. Object libraries and
build-time generator executables use normal CMake because they are internal
build artifacts, not fips deployment applications. Source lists come from the
upstream `sources.txt` manifests.

## Data and platform support

- Native Windows and Linux builds; CMake >= 3.21, Python 3 and a C++17 compiler.
- Cross-compilation is explicitly rejected: the current build must execute ICU's
  native data tools. A future cross-build needs a separate host-tool stage.
- Full default ICU data is generated from this exact checkout and embedded in a
  static library. No downloaded, mismatched data archive, ICU DLL or runtime
  `.dat` file is needed.
- Bootstrap libraries use upstream stub data to build the generators; final
  application libraries link the complete generated data. Code objects are reused.
- The first build compiles tools and generates all locales; this is significantly
  slower than later incremental builds.
- ICU exceptions and RTTI are enabled only on its own targets, even when a fips application
  disables them globally. Known upstream MSVC UBool/printf warnings are suppressed
  only on the affected ICU targets so fips warning-as-error builds work.
- Import only in graphical-client builds. ICU is not a server dependency.

The build intentionally retains complete data initially. Reducing locale and
feature data can be a separate measured change without sacrificing required
scripts or break rules.

## Verification and size

Run the sibling `fips-harfbuzz/fips-files/smoke` project. It tests shaping,
rasterization, bidi, grapheme/line boundaries and Persian number formatting
without configuring any ICU data path.

Initial Windows x64 Release measurements: embedded data 32.0 MiB; combined
FreeType/HarfBuzz/ICU smoke executable 35.4 MiB. Static archive sizes are not the
same as final application size because the linker discards unused code.

Tested source base: `e86daaca40` (ICU 79.1 development tree). This follows the
user's fork; it is not a claim that the checkout is a released stable tag.
Pin the eventual integration commit in consumers after committing/pushing.
