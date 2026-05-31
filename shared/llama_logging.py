import ctypes
import llama_cpp

# C 函数签名:
# void callback(int level, const char * message, void * user_data)
_LOG_CALLBACK_TYPE = ctypes.CFUNCTYPE(
    None,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_void_p,
)

# 保留一个模块级引用,使其不会被垃圾回收
_silent_callback_ref = None


def disable_llama_logging():
    """
    禁用所有 llama.cpp / ggml 的原生日志(Metal、CUDA、CPU)。

    必须在创建任何 Llama 实例之前调用一次。
    """
    global _silent_callback_ref

    def _silent_log(level, message, user_data):
        return

    _silent_callback_ref = _LOG_CALLBACK_TYPE(_silent_log)
    llama_cpp.llama_log_set(_silent_callback_ref, None)