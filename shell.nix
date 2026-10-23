{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [ pkgs.uv pkgs.poppler-utils pkgs.tesseract ];
  # CP-SAT/NumPy wheels need a C++ runtime on NixOS. This is project-scoped.
  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.zlib ];
}
