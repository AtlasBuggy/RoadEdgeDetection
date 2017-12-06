nix-shell -p 'python35Packages.opencv3.override {enableFfmpeg = true;}' python35Packages.matplotlib
