{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3.withPackages (ps: [ ps.tkinter ]);
in
pkgs.mkShell {
  packages = [
    python
    pkgs.git
    pkgs.gnumake
  ];

  shellHook = ''
    echo "8BitCPU Toolkit dev shell"
    echo "Python: $(python --version)"
    echo "Useful commands:"
    echo "  make test"
    echo "  make assemble-examples"
    echo "  make run-multiplication"
    echo "  make run-multiplication-bin"
    echo "  make gui-multiplication"
  '';
}
