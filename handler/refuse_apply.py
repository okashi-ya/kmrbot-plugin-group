import datetime
from protocol_adapter.adapter_type import AdapterGroupRequestEvent, AdapterGroupMessageEvent, AdapterBot
from protocol_adapter.protocol_adapter import ProtocolAdapter
from nonebot import on_request
from utils.permission import white_list_handle
from ..database.group_data import DBPluginsGroupData


def is_in_black_list(
        bot: AdapterBot,
        event: AdapterGroupMessageEvent):
    msg_type_id = ProtocolAdapter.get_msg_type_id(event)
    black_list = DBPluginsGroupData.get_user_black_list("group", msg_type_id)
    user_id = ProtocolAdapter.get_user_id(event)
    return user_id in black_list


refuse_apply = on_request(priority=5, rule=is_in_black_list, block=False)  # 调低相应级别
refuse_apply.handle(white_list_handle("group"))


@refuse_apply.handle()
async def _(
        bot: AdapterBot,
        event: AdapterGroupMessageEvent):
    bot_id = ProtocolAdapter.get_bot_id(bot)
    return await ProtocolAdapter.refuse_group_apply(bot_id, event)
