cmake_minimum_required(VERSION 3.15)
project(cmake_wrapper)

# TODO:
# - It should be find_package(SPIRV-Tools-opt REQUIRED CONFIG), but it can't be
#   modeled yet in spirv-tools recipe.
# - Upstream CMakeLists is not very neat, and doesn't always link
#   Spirv-Tools-opt in all required targets. Keep in mind that it works thanks
#   to global injection of include dirs/interface definitions from
#   conan_basic_setup(). It won't work without patches when moving to
#   CMakeToolchain + CMakeDeps.
if(ENABLE_OPT)
    find_package(SPIRV-Tools REQUIRED CONFIG)
endif()

add_subdirectory(src)
