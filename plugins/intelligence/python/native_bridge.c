/**
 * 邮件智能分析插件 —— Native 接口层
 *
 * 提供 C ABI 接口，使其他语言（C++、Go、Java 等）能调用 Python 分析引擎。
 *
 * 导出的函数：
 *   analyze_email_json()     — 分析邮件，返回 JSON 结果
 *   get_plugin_version()     — 获取插件版本号
 *   get_plugin_info()        — 获取插件元信息（JSON）
 *   set_analyze_timeout_ms() — 设置分析超时（毫秒）
 *   free_analyze_result()    — 释放结果字符串
 *   shutdown_python()        — 清理 Python 解释器
 *
 * 线程安全：当前实现不是线程安全的。多线程调用时需要外部加锁。
 *
 * 错误处理：
 *   所有 C 接口函数在 Python 异常时均返回 JSON 格式的错误响应，
 *   包含 "code" 和 "message" 字段，遵循 plugin-contract.md 的错误码约定。
 */

#include <Python.h>
#include <stdlib.h>
#include <string.h>

/* 模块名和函数名 */
#define MODULE_NAME "src.plugin_entry"
#define FUNC_NAME "analyze_email_json"

/* 保存上一次返回的结果字符串，供 free_analyze_result 释放 */
static char* _last_result = NULL;

/* 分析超时（毫秒），0 表示不超时，默认 2000ms（符合 07-intelligent-mail-management.md 建议） */
static long _timeout_ms = 2000;


/**
 * 执行一段 Python 代码并忽略异常。
 */
static void _py_run_simple(const char* code) {
    PyRun_SimpleString(code);
    PyErr_Clear();
}


/**
 * 初始化 Python 解释器并导入模块。
 * 仅第一次调用时执行初始化，后续调用直接返回。
 */
static int _ensure_python_initialized(void) {
    static int initialized = 0;
    if (initialized) {
        return 0;
    }

    Py_Initialize();
    if (!Py_IsInitialized()) {
        return -1;
    }

    /* 将插件根目录加入 sys.path，使 from src.plugin_entry import ... 能工作 */
    _py_run_simple("import sys; sys.path.insert(0, '.')");

    /* 注入超时工具函数，供 analyze_email_json 内部使用 */
    _py_run_simple(
        "import signal\n"
        "def _plugin_timeout_handler(signum, frame):\n"
        "    raise TimeoutError('PLUGIN_DNS_TIMEOUT: 分析超时')\n"
    );

    initialized = 1;
    return 0;
}


/**
 * 分析邮件并返回 JSON 结果。
 *
 * @param request_json  JSON 格式的邮件数据字符串
 * @return              JSON 格式的分析结果字符串（由本库管理内存，调用方不应 free）
 *
 * 调用方在处理完结果后应调用 free_analyze_result() 释放内存。
 * 如果不调用，下一次 analyze_email_json() 调用时会自动释放上一次的结果。
 */
const char* analyze_email_json(const char* request_json) {
    PyObject* pModule = NULL;
    PyObject* pFunc = NULL;
    PyObject* pArgs = NULL;
    PyObject* pResult = NULL;
    const char* result_str = NULL;

    /* 释放上一次的结果 */
    if (_last_result) {
        free(_last_result);
        _last_result = NULL;
    }

    /* 确保 Python 已初始化 */
    if (_ensure_python_initialized() != 0) {
        _last_result = strdup(
            "{\"pluginVersion\":\"0.1.0\",\"code\":\"PLUGIN_INTERNAL_500\","
            "\"message\":\"Python 解释器初始化失败\"}"
        );
        return _last_result;
    }

    /* 设置超时（Unix: signal.alarm, Windows: 无原生支持，留待 Python 层处理） */
    if (_timeout_ms > 0) {
        /* 转换为秒，向上取整 */
        int sec = (int)((_timeout_ms + 999) / 1000);
        char cmd[128];
        Py_ssize_t n = snprintf(cmd, sizeof(cmd),
            "try: signal.signal(signal.SIGALRM, _plugin_timeout_handler); "
            "signal.alarm(%d)\n"
            "except AttributeError: pass\n", sec);
        if (n > 0 && (size_t)n < sizeof(cmd)) {
            _py_run_simple(cmd);
        }
    }

    /* 导入模块 */
    pModule = PyImport_ImportModule(MODULE_NAME);
    if (!pModule) {
        PyErr_Clear();
        _last_result = strdup(
            "{\"pluginVersion\":\"0.1.0\",\"code\":\"PLUGIN_INTERNAL_500\","
            "\"message\":\"导入 src.plugin_entry 失败\"}"
        );
        return _last_result;
    }

    /* 获取函数 */
    pFunc = PyObject_GetAttrString(pModule, FUNC_NAME);
    if (!pFunc || !PyCallable_Check(pFunc)) {
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
        PyErr_Clear();
        _last_result = strdup(
            "{\"pluginVersion\":\"0.1.0\",\"code\":\"PLUGIN_INTERNAL_500\","
            "\"message\":\"函数 analyze_email_json 未找到\"}"
        );
        return _last_result;
    }

    /* 构造参数 */
    pArgs = PyUnicode_FromString(request_json);
    if (!pArgs) {
        Py_DECREF(pFunc);
        Py_DECREF(pModule);
        PyErr_Clear();
        _last_result = strdup(
            "{\"pluginVersion\":\"0.1.0\",\"code\":\"PLUGIN_VALIDATION_400\","
            "\"message\":\"参数转换失败\"}"
        );
        return _last_result;
    }

    /* 调用 Python 函数 */
    pResult = PyObject_CallOneArg(pFunc, pArgs);
    Py_DECREF(pArgs);

    /* 取消超时（Unix） */
    if (_timeout_ms > 0) {
        _py_run_simple(
            "try: signal.alarm(0)\n"
            "except AttributeError: pass\n"
        );
    }

    if (!pResult) {
        /* 检查是否是超时异常 */
        PyObject* pExcType = NULL;
        PyObject* pExcValue = NULL;
        PyObject* pExcTraceback = NULL;
        PyErr_Fetch(&pExcType, &pExcValue, &pExcTraceback);

        const char* err_code = "PLUGIN_INTERNAL_500";
        const char* err_msg = "Python 函数调用失败";

        if (pExcValue) {
            PyObject* pStr = PyObject_Str(pExcValue);
            if (pStr) {
                const char* msg = PyUnicode_AsUTF8(pStr);
                if (msg && strstr(msg, "PLUGIN_DNS_TIMEOUT") != NULL) {
                    err_code = "PLUGIN_DNS_TIMEOUT";
                    err_msg = "分析超时";
                } else if (msg) {
                    err_msg = msg;
                }
                Py_DECREF(pStr);
            }
        }

        /* 构造错误 JSON */
        char err_buf[512];
        Py_ssize_t n = snprintf(err_buf, sizeof(err_buf),
            "{\"pluginVersion\":\"0.1.0\",\"code\":\"%s\",\"message\":\"%s\","
            "\"spam\":{\"label\":\"unknown\",\"score\":0.0},"
            "\"priority\":{\"label\":\"normal\",\"score\":0.0,\"reasons\":[]},"
            "\"risk\":{\"level\":\"none\",\"score\":0.0,\"indicators\":[]},"
            "\"actions\":[]}",
            err_code, err_msg);
        if (n > 0 && (size_t)n < sizeof(err_buf)) {
            _last_result = strdup(err_buf);
        }

        Py_XDECREF(pExcType);
        Py_XDECREF(pExcValue);
        Py_XDECREF(pExcTraceback);
        Py_DECREF(pFunc);
        Py_DECREF(pModule);
        return _last_result ? _last_result : "{}";
    }

    /* 把 Python 字符串转成 C 字符串 */
    {
        const char* tmp = PyUnicode_AsUTF8(pResult);
        if (tmp) {
            _last_result = strdup(tmp);
            result_str = _last_result;
        }
    }

    Py_DECREF(pResult);
    Py_DECREF(pFunc);
    Py_DECREF(pModule);

    if (!result_str) {
        _last_result = strdup(
            "{\"pluginVersion\":\"0.1.0\",\"code\":\"PLUGIN_INTERNAL_500\","
            "\"message\":\"结果转换失败\"}"
        );
    }

    return _last_result;
}


/**
 * 获取插件版本号。
 *
 * @return 版本号字符串（如 "0.1.0"），由本库管理内存，调用方不应 free。
 */
const char* get_plugin_version(void) {
    if (_ensure_python_initialized() != 0) {
        return "0.1.0";
    }

    /* 从 Python _version 模块获取 */
    _py_run_simple(
        "import __main__\n"
        "__main__.__plugin_version_for_c__ = __import__('src._version').__version__\n"
    );

    PyObject* pMain = PyImport_AddModule("__main__");
    if (pMain) {
        PyObject* pVer = PyObject_GetAttrString(pMain, "__plugin_version_for_c__");
        if (pVer && PyUnicode_Check(pVer)) {
            const char* ver = PyUnicode_AsUTF8(pVer);
            if (ver) {
                if (_last_result) free(_last_result);
                _last_result = strdup(ver);
                Py_DECREF(pVer);
                return _last_result;
            }
            Py_DECREF(pVer);
        } else {
            Py_XDECREF(pVer);
        }
        PyErr_Clear();
    }

    return "0.1.0";
}


/**
 * 获取插件元信息（JSON 格式）。
 *
 * @return JSON 字符串，包含版本号、能力列表、超时配置等。
 */
const char* get_plugin_info(void) {
    const char* ver = get_plugin_version();
    char buf[512];
    Py_ssize_t n = snprintf(buf, sizeof(buf),
        "{"
        "\"pluginVersion\":\"%s\","
        "\"capabilities\":[\"spam\",\"priority\",\"risk\",\"html_analysis\","
        "\"header_analysis\",\"reputation\"],"
        "\"timeoutMs\":%ld,"
        "\"abi\":\"const char* analyze_email_json(const char*)\""
        "}",
        ver, _timeout_ms);
    if (n > 0 && (size_t)n < sizeof(buf)) {
        if (_last_result) free(_last_result);
        _last_result = strdup(buf);
        return _last_result;
    }
    return "{}";
}


/**
 * 设置分析超时时间。
 *
 * @param timeout_ms 超时毫秒数（0 表示不超时）
 */
void set_analyze_timeout_ms(long timeout_ms) {
    _timeout_ms = timeout_ms;
}


/**
 * 释放上一次返回的结果字符串。
 *
 * 调用 analyze_email_json() 返回的字符串由本库管理，
 * 调用方在处理完结果后应调用此函数释放内存。
 * 如果不调用，下一次 analyze_email_json() 调用时会自动释放上一次的结果。
 */
void free_analyze_result(void) {
    if (_last_result) {
        free(_last_result);
        _last_result = NULL;
    }
}


/**
 * 清理 Python 解释器。
 * 在程序退出时调用，释放 Python 解释器占用的资源。
 */
void shutdown_python(void) {
    free_analyze_result();
    if (Py_IsInitialized()) {
        Py_Finalize();
    }
}
