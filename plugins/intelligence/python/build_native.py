#!/usr/bin/env python3
"""
Native 动态库构建脚本。

将 Python 邮件分析引擎编译为 C 动态库（.dll / .so），
供其他语言（C++、Go、Java 等）通过 C ABI 调用。

用法：
    python build_native.py              # 自动检测平台编译
    python build_native.py --debug      # 调试模式，包含符号信息

依赖：
    - Python 开发头文件（Windows: Visual Studio Build Tools / Linux: python3-dev）
    - C 编译器（Windows: MSVC / Linux: gcc）
"""

import hashlib
import os
import shutil
import subprocess
import sys
import sysconfig
import platform

from src._version import __version__


def get_python_include_dir() -> str:
    """获取 Python 头文件路径（如 Include/）。"""
    # sysconfig 比 sys.prefix + "include" 更可靠
    incdir = sysconfig.get_config_var("INCLUDEPY")
    if incdir and os.path.isdir(incdir):
        return incdir
    # 回退方案
    fallback = os.path.join(sys.prefix, "include")
    if os.path.isdir(fallback):
        return fallback
    return incdir or ""


def get_python_lib_dir() -> str:
    """获取 Python 库文件路径（如 libs/python3.lib）。"""
    # Windows 下 python3.lib / python313.lib 在 libs/ 下
    # Linux 下 libpython3.x.so 在 LIBDIR 下
    libdir = sysconfig.get_config_var("LIBDIR")
    if not libdir or not os.path.isdir(libdir):
        # 回退到 prefix/lib
        libdir = os.path.join(sys.prefix, "libs" if sys.platform == "win32" else "lib")
    return libdir if os.path.isdir(libdir) else ""


def get_python_lib_name() -> str:
    """获取 Python 库名（Windows: python3XX, Linux: python3.X）。"""
    # LDLIBRARY 通常是 "libpython3.13.so" 或 "python3.dll"
    ldlib = sysconfig.get_config_var("LDLIBRARY")
    if ldlib:
        # 去掉 lib前缀 和 .so/.dll 后缀
        name = ldlib
        if name.startswith("lib"):
            name = name[3:]
        for ext in [".so", ".dll", ".a", ".dylib"]:
            if name.endswith(ext):
                name = name[: -len(ext)]
        if name:
            return name
    # 回退：用 python3 + 版本后缀
    ver = sysconfig.get_config_var("VERSION")
    return f"python{ver}" if ver else "python3"


def get_compiler() -> str:
    """选择合适的 C 编译器。"""
    if sys.platform == "win32":
        # Windows: 优先用 MSVC（cl.exe），回退到 gcc
        msvc = shutil.which("cl")
        if msvc:
            return "cl"
        gcc = shutil.which("gcc")
        if gcc:
            return "gcc"
    elif sys.platform == "darwin":
        return shutil.which("clang") or "clang"
    return shutil.which("gcc") or "gcc"


def get_output_name() -> str:
    """根据平台生成输出文件名。"""
    base = "intelligence_plugin"
    if sys.platform == "win32":
        return f"{base}.dll"
    elif sys.platform == "darwin":
        return f"{base}.dylib"
    return f"{base}.so"


def get_cflags(debug: bool = False) -> list[str]:
    """构造 C 编译器标志。"""
    cflags = [
        f"-I{get_python_include_dir()}",
    ]
    if debug:
        cflags.extend(["-g", "-O0"])
    else:
        cflags.extend(["-O2", "-DNDEBUG"])
    if sys.platform == "win32":
        cflags.append("-DWIN32")
        if shutil.which("cl"):
            cflags.append("/MD")   # MSVC 多线程 DLL
        else:
            # MinGW GCC
            cflags.append("-D__USE_MINGW_ANSI_STDIO=1")
    else:
        cflags.extend(["-fPIC", "-std=c11"])
    return cflags


def get_lflags(debug: bool = False) -> list[str]:
    """构造链接器标志。"""
    lflags = []
    lib_name = get_python_lib_name()
    if sys.platform == "win32":
        lib_dir = get_python_lib_dir()
        if shutil.which("cl"):
            # MSVC
            lib_path = os.path.join(lib_dir, f"{lib_name}.lib")
            if os.path.isfile(lib_path):
                lflags.append(lib_path)
            else:
                # 尝试 python3.lib
                alt = os.path.join(lib_dir, "python3.lib")
                if os.path.isfile(alt):
                    lflags.append(alt)
                else:
                    # 尝试 python313.lib
                    ver_lib = os.path.join(lib_dir, f"python{sys.version_info.major}{sys.version_info.minor}.lib")
                    if os.path.isfile(ver_lib):
                        lflags.append(ver_lib)
                    else:
                        print(f"  [警告] 未找到 Python 库文件，尝试 -l{lib_name}")
                        lflags.append(f"-l{lib_name}")
            # MSVC 不需要额外标志
            lflags.append("/DLL")
            lflags.append("/EXPORT:analyze_email_json")
            lflags.append("/EXPORT:free_analyze_result")
            lflags.append("/EXPORT:shutdown_python")
        else:
            # MinGW GCC
            lflags.append(f"-L{lib_dir}")
            lflags.append(f"-l{lib_name}")
            lflags.append("-shared")
            lflags.append("-Wl,--out-implib,libintelligence_plugin.a")
    else:
        # Linux / macOS
        lib_dir = get_python_lib_dir()
        lflags.append(f"-L{lib_dir}")
        lflags.append(f"-l{lib_name}")
        lflags.append("-shared")
        if sys.platform == "darwin":
            lflags.extend(["-undefined", "dynamic_lookup"])
    return lflags


def build(debug: bool = False) -> bool:
    """执行编译。"""
    source = "native_bridge.c"
    output = get_output_name()
    compiler = get_compiler()

    if not compiler:
        print("[错误] 未找到 C 编译器。请安装:")
        print("  Windows: Visual Studio Build Tools 或 MinGW-w64")
        print("  Linux:   apt install gcc python3-dev")
        print("  macOS:   xcode-select --install")
        return False

    if not os.path.isfile(source):
        print(f"[错误] 找不到源文件 {source}")
        print(f"        请确认当前目录是 python/")
        return False

    inc_dir = get_python_include_dir()
    if not inc_dir:
        print("[错误] 找不到 Python 头文件。请安装 Python 开发包:")
        print("  Windows: 重新运行 Python 安装程序，勾选 'Development Headers'")
        print("  Linux:   apt install python3-dev")
        print("  macOS:   重新安装 Python 或 xcode-select --install")
        return False

    print(f"[构建] 编译器:    {compiler}")
    print(f"[构建] 目标:      {output}")
    print(f"[构建] Python:    {sys.version}")
    print(f"[构建] 头文件:    {inc_dir}")
    print(f"[构建] 库文件:    {get_python_lib_dir()}")
    print(f"[构建] 模式:      {'debug' if debug else 'release'}")
    print()

    cflags = get_cflags(debug)
    lflags = get_lflags(debug)

    cmd = [compiler] + cflags + [source] + lflags + [f"-o{output}"]

    print(f"[执行] {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        print(f"[错误] 编译失败（exit code {result.returncode}）")
        return False

    if os.path.isfile(output):
        size = os.path.getsize(output)
        print(f"[成功] {output} ({size / 1024:.1f} KB)")

        # 计算 SHA-256 校验和
        sha256 = hashlib.sha256()
        with open(output, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        checksum = sha256.hexdigest()
        checksum_file = f"{output}.sha256"
        with open(checksum_file, "w") as f:
            f.write(f"{checksum}  {output}\n")
        print(f"[校验和] {checksum_file} -> {checksum[:16]}...")

        # 生成 version.txt
        with open("plugin_version.txt", "w") as f:
            f.write(f"{__version__}\n")
        print(f"[版本]   plugin_version.txt -> {__version__}")

        return True

    print("[警告] 编译完成但未找到输出文件")
    return False


def clean():
    """清理构建产物。"""
    patterns = [
        "intelligence_plugin.*",
        "*.obj",
        "*.exp",
        "*.lib",
        "*.pdb",
        "libintelligence_plugin.a",
        "__pycache__",
    ]
    for pattern in patterns:
        for f in __import__("glob").glob(pattern):
            if os.path.isfile(f):
                os.remove(f)
                print(f"  [清理] 删除 {f}")
            elif os.path.isdir(f):
                shutil.rmtree(f)
                print(f"  [清理] 删除目录 {f}/")
    print("[清理] 完成")


def print_help():
    print(__doc__)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--help", "-h", "help"):
            print_help()
        elif arg in ("--clean", "clean"):
            clean()
        elif arg in ("--debug", "debug"):
            build(debug=True)
        else:
            print(f"未知参数: {arg}")
            print_help()
    else:
        build(debug=False)
