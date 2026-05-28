/**
 * 邮件智能分析插件 —— Native 接口层
 *
 * 提供 C ABI 接口，使其他语言（C++、Go、Java 等）能调用 Python 分析引擎。
 *
 * 导出的函数：
 *   const char* analyze_email_json(const char* request_json)
 *
 * 使用方式：
 *   编译为动态库（.dll / .so），加载后调用 analyze_email_json()。
 *   返回的字符串由本库管理，调用方应调用 free_analyze_result() 释放。
 */

#include <Python.h>
#include <stdlib.h>
#include <string.h>

/* 模块名和函数名 */
#define MODULE_NAME "src.plugin_entry"
#define FUNC_NAME "analyze_email_json"

/* 保存上一次返回的结果字符串，供 free_analyze_result 释放 */
static char* _last_result = NULL;


/**
 * 初始化 Python 解释器并导入模块。
 * 在第一次调用 analyze_email_json 时自动执行。
 */
static int _ensure_python_initialized(void) {
    static int initialized = 0;
    if (initialized) {
        return 0;
    }

    /* 初始化 Python 解释器 */
    Py_Initialize();
    if (!Py_IsInitialized()) {
        return -1;
    }

    /* 将 src/ 目录加入 sys.path，使 from src.plugin_entry import ... 能工作 */
    PyRun_SimpleString(
        "import sys; sys.path.insert(0, '.')"
    );

    initialized = 1;
    return 0;
}


/**
 * 分析邮件并返回 JSON 结果。
 *
 * @param request_json  JSON 格式的邮件数据字符串
 * @return              JSON 格式的分析结果字符串（由本库管理内存）
 *
 * 线程安全：当前实现不是线程安全的。多线程调用时需要加锁。
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
        return "{\"error\": \"Failed to initialize Python interpreter\"}";
    }

    /* 导入模块 */
    pModule = PyImport_ImportModule(MODULE_NAME);
    if (!pModule) {
        PyErr_Clear();
        return "{\"error\": \"Failed to import src.plugin_entry\"}";
    }

    /* 获取函数 */
    pFunc = PyObject_GetAttrString(pModule, FUNC_NAME);
    if (!pFunc || !PyCallable_Check(pFunc)) {
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
        PyErr_Clear();
        return "{\"error\": \"Function analyze_email_json not found\"}";
    }

    /* 构造参数：把 C 字符串转成 Python 字符串 */
    pArgs = PyUnicode_FromString(request_json);
    if (!pArgs) {
        Py_DECREF(pFunc);
        Py_DECREF(pModule);
        PyErr_Clear();
        return "{\"error\": \"Failed to convert argument\"}";
    }

    /* 调用 Python 函数 */
    pResult = PyObject_CallOneArg(pFunc, pArgs);
    Py_DECREF(pArgs);

    if (!pResult) {
        Py_DECREF(pFunc);
        Py_DECREF(pModule);
        PyErr_Clear();
        return "{\"error\": \"Python function call failed\"}";
    }

    /* 把 Python 字符串转成 C 字符串 */
    {
        const char* tmp = PyUnicode_AsUTF8(pResult);
        if (tmp) {
            _last_result = strdup(tmp);
            result_str = _last_result;
        } else {
            result_str = "{\"error\": \"Failed to convert result\"}";
        }
    }

    Py_DECREF(pResult);
    Py_DECREF(pFunc);
    Py_DECREF(pModule);

    return result_str ? result_str : "{\"error\": \"Unknown error\"}";
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
