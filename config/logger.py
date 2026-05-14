"""日志配置，统一接管标准 logging 到 loguru"""
import logging
import sys
from loguru import logger


class InterceptHandler(logging.Handler):
    """将标准库 logging 重定向到 loguru"""

    def emit(self, record: logging.LogRecord):
        # 一、映射日志级别
        # 1、尝试按名称匹配 loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            # 2、回退到数字级别
            level = record.levelno

        # 二、定位调用栈
        # 1、跳过 logging 模块自身的帧
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        # 2、用 loguru 输出，保留原始异常信息
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# 一、移除默认 handler
logger.remove()

# 二、控制台输出
# 1、带颜色，格式紧凑
# 2、级别 >= INFO 才显示
logger.add(
    sys.stderr,
    format="<green>{time:MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# 三、文件输出
# 1、按天轮转，保留 30 天
# 2、纯文本格式，级别 >= DEBUG
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    level="DEBUG",
)

# 四、接管标准 logging
# 1、uvicorn、sqlalchemy 等库的输出统一走 loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
