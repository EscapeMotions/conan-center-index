from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "VirtualRunEnv"
    test_type = "explicit"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_CHIMERA"] = self.dependencies["vectorscan"].options.with_chimera
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindirs[0], "hs_example")
            self.run(bin_path, env="conanrun")

            if self.dependencies["vectorscan"].options.with_chimera:
                bin_path = os.path.join(self.cpp.build.bindirs[0], "ch_example")
                self.run(bin_path, env="conanrun")
