import datetime
from protocol_adapter.adapter_type import AdapterGroupMessageEvent
from protocol_adapter.protocol_adapter import ProtocolAdapter
from nonebot import on_command
from nonebot.log import logger
from utils import group_only, get_time_zone
from utils.permission import white_list_handle

avoid_at = on_command(cmd="周表", priority=5, block=False)  # 调低相应级别
avoid_at.handle(white_list_handle("group"))


@avoid_at.handle()
async def _():
    logger.info("OK!")