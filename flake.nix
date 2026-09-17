{
  description = "Development shell for 8BitCPU Toolkit";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          python = pkgs.python3.withPackages (ps: [ ps.tkinter ]);
        in
        {
          default = pkgs.mkShell {
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
              echo "  make gui-multiplication"
            '';
          };
        });
    };
}
