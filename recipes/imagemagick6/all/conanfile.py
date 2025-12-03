import os
from conan import ConanFile
from conan.tools.gnu import Autotools, AutotoolsToolchain, PkgConfigDeps, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.files import get, rmdir, rm, copy, apply_conandata_patches
from conan.tools.scm import Version
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os, fix_apple_shared_install_name

class ImageMagick6Conan(ConanFile):
    name = "imagemagick6"
    description = (
        "ImageMagick is a free and open-source software suite for displaying, converting, and editing "
        "raster image and vector image files"
    )
    topics = ("imagemagick", "images", "manipulating")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://legacy.imagemagick.org"
    license = "ImageMagick"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "hdri": [True, False],
        "quantum_depth": [8, 16, 32],
        "with_zlib": [True, False],
        "with_bzlib": [True, False],
        "with_lzma": [True, False],
        "with_lcms": [True, False],
        "with_openexr": [True, False],
        "with_heic": [True, False],
        "with_jbig": [True, False],
        "with_jpeg": [None, "libjpeg", "libjpeg-turbo"],
        "with_openjp2": [True, False],
        "with_pango": [True, False],
        "with_png": [True, False],
        "with_tiff": [True, False],
        "with_webp": [True, False],
        "with_xml2": [True, False],
        "with_freetype": [True, False],
        "with_djvu": [True, False],
        "utilities": [True, False],
    }    
    default_options = {
        "shared": False,
        "fPIC": True,
        "hdri": True,
        "quantum_depth": 16,
        "with_zlib": True,
        "with_bzlib": True,
        "with_lzma": True,
        "with_lcms": True,
        "with_openexr": False,
        "with_heic": True,
        "with_jbig": True,
        "with_jpeg": "libjpeg",
        "with_openjp2": True,
        "with_pango": False,
        "with_png": True,
        "with_tiff": True,
        "with_webp": True,
        "with_xml2": False,
        "with_freetype": False,
        "with_djvu": False,
        "utilities": True,
    }
    # exports_sources = "patches/*"

    @property
    def _modules(self):
        # These are the core library modules of ImageMagick
        return ["MagickCore", "MagickWand", "Magick++"]

    def layout(self):
        basic_layout(self, src_folder="source")
        # For Autotools, build files can be generated in the source folder if it's an in-source build,
        # or in self.build_folder for out-of-source. ImageMagick supports out-of-source.
        # If configure script is in source_folder, Autotools(self) will handle it.

    def config_options(self):
        if self.settings.os == "Windows":
            # This recipe is not intended for Windows IM6 build via Autotools.
            # VisualMagick or MSYS2/Autotools would be needed.
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        # For C++ bindings, if not building them, you might not need a C++ compiler.
        # However, Magick++ is C++, so compiler.cppstd and libcxx would be relevant if it's built.
        # For simplicity, assuming C sources or that dependencies handle C++ standard.

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration(
                "This recipe currently supports ImageMagick 6 on macOS (and Linux) via Autotools. "
                "Windows build is not supported with this configuration."
            )
        if self.options.with_pango and self.settings.os == "Macos":
            self.output.warning("Building ImageMagick with Pango on macOS might require X11/Quartz or specific setup.")
        if self.options.with_djvu:
            self.output.warning("Conan package for DjVuLibre is not commonly available. Ensure it's system-installed if this option is True.")

    def requirements(self):
        if self.options.with_zlib:
            self.requires("zlib/1.3.1")
        if self.options.with_bzlib:
            self.requires("bzip2/1.0.8")
        if self.options.with_lzma:
            self.requires("xz_utils/[>=5.4.5 <6]")
        if self.options.with_lcms:
            self.requires("lcms/2.16")
        if self.options.with_openexr:
            self.requires("openexr/3.1.9") # IM6 might need OpenEXR 2.x. Test carefully. e.g. 2.5.7
        if self.options.with_heic:
            self.requires("libheif/[>=1.16.2 <2]")
        if self.options.with_jbig:
            self.requires("jbig/20160605")
        if self.options.with_jpeg == "libjpeg":
            self.requires("libjpeg/9e")
        elif self.options.with_jpeg == "libjpeg-turbo":
            self.requires("libjpeg-turbo/3.0.3")
        if self.options.with_openjp2:
            self.requires("openjpeg/[>=2.5.2 <3]")
        if self.options.with_pango:
            self.requires("pango/1.50.14") # This is quite new for IM6, might need older.
        if self.options.with_png:
            self.requires("libpng/[>=1.6.48 <2]")
        if self.options.with_tiff:
            self.requires("libtiff/[>=4.6.0 <5]")
            self.requires("zstd/1.5.7")
        if self.options.with_webp:
            self.requires("libwebp/[>=1.3.2 <2]")
        if self.options.with_xml2:
            self.requires("libxml2/2.12.7")
        if self.options.with_freetype:
            self.requires("freetype/2.13.2")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)


    def generate(self):
        # Dependency virtual environments
        PkgConfigDeps(self).generate()
        deps = AutotoolsDeps(self)
        deps.generate()

        # AutotoolsToolchain to prepare configure arguments
        tc = AutotoolsToolchain(self)

        def yes_no(opt_value):
            return "yes" if opt_value else "no"

        configure_args = [
            "--disable-openmp",
            "--disable-opencl",
            "--disable-docs",
            "--with-perl=no",
            "--with-x=no", # Crucial for macOS if X11 is not desired/installed
            "--with-fontconfig={}".format(yes_no(self.options.with_pango)), # Fontconfig is often a dep of Pango
            "--without-dps",
            "--without-fftw",
            "--without-fpx",
            "--without-raw",
            "--without-wmf", # Windows Metafile, less relevant for macOS
            f"--enable-shared={yes_no(self.options.shared)}",
            f"--enable-static={yes_no(not self.options.shared)}",
            f"--enable-hdri={yes_no(self.options.hdri)}",
            f"--with-quantum-depth={self.options.quantum_depth}",
            f"--with-zlib={yes_no(self.options.with_zlib)}",
            f"--with-bzlib={yes_no(self.options.with_bzlib)}",
            f"--with-lzma={yes_no(self.options.with_lzma)}",
            f"--with-lcms={yes_no(self.options.with_lcms)}",
            f"--with-openexr={yes_no(self.options.with_openexr)}",
            f"--with-heic={yes_no(self.options.with_heic)}",
            f"--with-jbig={yes_no(self.options.with_jbig)}",
            f"--with-jpeg={yes_no(self.options.with_jpeg)}",
            f"--with-openjp2={yes_no(self.options.with_openjp2)}",
            f"--with-pango={yes_no(self.options.with_pango)}",
            f"--with-png={yes_no(self.options.with_png)}",
            f"--with-tiff={yes_no(self.options.with_tiff)}",
            f"--with-webp={yes_no(self.options.with_webp)}",
            f"--with-xml={yes_no(self.options.with_xml2)}", # IM uses --with-xml for libxml2
            f"--with-freetype={yes_no(self.options.with_freetype)}",
            f"--with-djvu={yes_no(self.options.with_djvu)}",
            f"--with-utilities={yes_no(self.options.utilities)}",
        ]

        # On macOS, it might be necessary to point to specific dependency locations
        # if pkg-config doesn't pick them up correctly, e.g. for freetype or libjpeg.
        # However, PkgConfigDeps should handle this.

        # If building on macOS for Apple Silicon, Autotools might need help finding tools
        # tc.apple_arch_flag = True # If issues arise with architecture detection

        if is_apple_os(self) and self.options.shared:
            # Inject -headerpad_max_install_names for shared library, otherwise fix_apple_shared_install_name() may fail.
            # tc.extra_ldflags.append("-headerpad_max_install_names")
            tc.extra_ldflags.append("-Wl,-headerpad_max_install_names")
            # tc.extra_linker_flags.append("-Wl,-headerpad_max_install_names")

        tc.make_args.append("V=1")
        tc.configure_args.extend(configure_args)
        tc.generate()

    def build(self):
        apply_conandata_patches(self) # Apply patches if any are defined in conandata.yml and exported

        # The configure script is in self.source_folder
        # Autotools helper will run configure and make
        autotools = Autotools(self)
        autotools.configure() # Reads args from AutotoolsToolchain
        autotools.make()

    def package(self):
        # Copy license
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"), keep_path=False, ignore_case=True)


        autotools = Autotools(self)
        autotools.install() # This will install to self.package_folder

        if is_apple_os(self):
            fix_apple_shared_install_name(self)

        # Remove unwanted files and folders
        # Pkgconfig files might be useful, but original recipe removed them.
        # If using PkgConfigDeps downstream, these .pc files can be helpful if correct.
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "share", "doc"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))
        # Remove .la files (libtool archive files)
        rm(self, "*.la", os.path.join(self.package_folder, "lib"), recursive=True)

        # The headers are installed by `make install` into include/ImageMagick-6/
        # If they are not, manual copying would be needed:
        # im_version_major = Version(self.version).major # This will be "6"
        # header_dir_im = os.path.join(self.package_folder, "include", f"ImageMagick-{im_version_major}")
        # for module in self._modules:
        #     module_header_src = os.path.join(self.source_folder, module)
        #     module_header_dst = os.path.join(header_dir_im, module)
        #     copy(self, "*.h", src=module_header_src, dst=module_header_dst)

    def _libname(self, library_base_name):
        # library_base_name is "MagickCore", "MagickWand", "Magick++"
        # For ImageMagick 6, typical library names are like:
        # libMagickCore-6.Q16.so, libMagickWand-6.Q16HDRI.a
        # This function should return the stem, e.g., "MagickCore-6.Q16HDRI"

        # Version major for IM6 is 6.
        # Example: self.version is "6.9.12-85", Version(self.version).major is "6"
        im_major = Version(self.version).major

        suffix = "HDRI" if self.options.hdri else ""
        # Note: Some IM6 versions might not include HDRI in the lib name even if enabled,
        # or might have a different convention. Verify with actual build output.
        return f"{library_base_name}-{im_major}.Q{self.options.quantum_depth}{suffix}"

    def package_info(self):
        im_version_major = Version(self.version).major
        imagemagick_include_subdir = os.path.join("include", f"ImageMagick-{im_version_major}")

        # MagickCore
        lib_magickcore = self._libname("MagickCore")
        self.cpp_info.components["MagickCore"].libs = [lib_magickcore]
        self.cpp_info.components["MagickCore"].includedirs = [os.path.join(imagemagick_include_subdir, "magick")] # [imagemagick_include_subdir]
        # Defines are important for consumers to know IM configuration
        self.cpp_info.components["MagickCore"].defines.extend([
            f"MAGICKCORE_QUANTUM_DEPTH={self.options.quantum_depth}",
            f"MAGICKCORE_HDRI_ENABLE={1 if self.options.hdri else 0}",
            "_MAGICKDLL_=1" if self.options.shared else "_MAGICKLIB_=1"
        ])
        if self.settings.os == "Linux": # And potentially other Unix-like systems
            self.cpp_info.components["MagickCore"].system_libs.append("pthread")

        # Set pkg-config name for this component. Actual .pc file might be MagickCore.pc or MagickCore-6.Q16.pc etc.
        # This needs to match the .pc file generated by ImageMagick's build.
        # For ImageMagick 6, it's often like "MagickCore-6.Q16" or just "MagickCore"
        # If the .pc files are named exactly as self._libname(...), then this is fine.
        # Otherwise, adjust to the actual .pc file names (without .pc extension).
        # Example: self.cpp_info.components["MagickCore"].set_property("pkg_config_name", "MagickCore")
        # Or, if versioned pc files:
        pc_config_name_magickcore = f"MagickCore-{im_version_major}.Q{self.options.quantum_depth}"
        if self.options.hdri and self.settings.os != "Windows": # HDRI suffix in .pc is common on Linux
             pc_config_name_magickcore += "HDRI" # Check actual .pc file name
        self.cpp_info.components["MagickCore"].set_property("pkg_config_name", pc_config_name_magickcore)


        # MagickWand
        lib_magickwand = self._libname("MagickWand")
        self.cpp_info.components["MagickWand"].libs = [lib_magickwand]
        self.cpp_info.components["MagickWand"].includedirs = [os.path.join(imagemagick_include_subdir, "wand")]
        self.cpp_info.components["MagickWand"].requires = ["MagickCore"]
        pc_config_name_magickwand = f"MagickWand-{im_version_major}.Q{self.options.quantum_depth}"
        if self.options.hdri and self.settings.os != "Windows":
             pc_config_name_magickwand += "HDRI"
        self.cpp_info.components["MagickWand"].set_property("pkg_config_name", pc_config_name_magickwand)

        # Magick++
        lib_magickpp = self._libname("Magick++")
        self.cpp_info.components["Magick++"].libs = [lib_magickpp]
        self.cpp_info.components["Magick++"].includedirs = [os.path.join(imagemagick_include_subdir, "Magick++"), imagemagick_include_subdir]
        self.cpp_info.components["Magick++"].requires = ["MagickWand"] # Magick++ uses MagickWand
        pc_config_name_magickpp = f"Magick++-{im_version_major}.Q{self.options.quantum_depth}"
        if self.options.hdri and self.settings.os != "Windows":
             pc_config_name_magickpp += "HDRI"
        self.cpp_info.components["Magick++"].set_property("pkg_config_name", pc_config_name_magickpp)


        # Add dependencies to components for pkg-config and cmake to know about them
        if self.options.with_zlib:
            self.cpp_info.components["MagickCore"].requires.append("zlib::zlib")
        if self.options.with_bzlib:
            self.cpp_info.components["MagickCore"].requires.append("bzip2::bzip2")
        if self.options.with_lzma:
            self.cpp_info.components["MagickCore"].requires.append("xz_utils::xz_utils")
        if self.options.with_lcms:
            self.cpp_info.components["MagickCore"].requires.append("lcms::lcms")
        # ... and so on for all other conditional dependencies ...
        if self.options.with_openexr:
            self.cpp_info.components["MagickCore"].requires.append("openexr::openexr")
        if self.options.with_heic:
            self.cpp_info.components["MagickCore"].requires.append("libheif::libheif")
        if self.options.with_jbig:
            self.cpp_info.components["MagickCore"].requires.append("jbig::jbig")
        if self.options.with_jpeg == "libjpeg":
            self.cpp_info.components["MagickCore"].requires.append("libjpeg::libjpeg")
        elif self.options.with_jpeg == "libjpeg-turbo":
            self.cpp_info.components["MagickCore"].requires.append("libjpeg-turbo::libjpeg-turbo")
        if self.options.with_openjp2:
            self.cpp_info.components["MagickCore"].requires.append("openjpeg::openjpeg")
        if self.options.with_pango:
             self.cpp_info.components["MagickCore"].requires.append("pango::pango")
        if self.options.with_png:
            self.cpp_info.components["MagickCore"].requires.append("libpng::libpng")
        if self.options.with_tiff:
            self.cpp_info.components["MagickCore"].requires.append("libtiff::libtiff")
            self.cpp_info.components["MagickCore"].requires.append("zstd::zstd")
        if self.options.with_webp:
            self.cpp_info.components["MagickCore"].requires.append("libwebp::libwebp")
        if self.options.with_xml2:
            self.cpp_info.components["MagickCore"].requires.append("libxml2::libxml2")
        if self.options.with_freetype:
            self.cpp_info.components["MagickCore"].requires.append("freetype::freetype")

        if self.options.utilities:
            # Add bin directory to PATH for utilities like 'convert', 'identify'
            # For consumers at build time (e.g. if they need to run 'convert' in their build scripts)
            # self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
            # For consumers at run time
            self.runenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))

        # To help CMake's find_package(ImageMagick)
        # The official FindImageMagick.cmake looks for components like "MagickCore", "MagickWand", "Magick++"
        # and also specific library names.
        self.cpp_info.set_property("cmake_file_name", "ImageMagick")
        self.cpp_info.set_property("cmake_target_name", "ImageMagick::MagickCore") # Main target often MagickCore

        self.cpp_info.components["MagickCore"].set_property("cmake_target_name", "ImageMagick::MagickCore")
        self.cpp_info.components["MagickWand"].set_property("cmake_target_name", "ImageMagick::MagickWand")
        self.cpp_info.components["Magick++"].set_property("cmake_target_name", "ImageMagick::Magick++")

        # TODO: The exact pkg-config names and CMake target names might need verification against
        # a typical ImageMagick 6 installation to ensure full compatibility with find_package and pkg-config.
