import copy
from nonebot import on_command
from nonebot.internal.matcher import Matcher
from protocol_adapter.protocol_adapter import ProtocolAdapter
from protocol_adapter.adapter_type import AdapterMessage, AdapterBot, AdapterMessageEvent, AdapterGroupMessageEvent
from nonebot.rule import to_me
from nonebot.params import ArgPlainText, CommandArg
from ..database.group_data import DBPluginsGroupData
from utils.permission import white_list_handle, only_me


async def anslysis_param(
    bot: AdapterBot,
    matcher: Matcher,
    event: AdapterMessageEvent,
    command_arg: AdapterMessage = CommandArg(),
):
    data = command_arg.extract_plain_text().split(" ")
    # 参数：（群号可选）
    if len(data) != 0 and len(data) != 1:
        return await matcher.finish(
            ProtocolAdapter.MS.reply(event) +
            ProtocolAdapter.MS.text("参数错误！参数列表：1.群号（可选） 2.userID"))
    params = copy.deepcopy(data)
    if len(params) == 1:
        if not isinstance(event, AdapterGroupMessageEvent):
            return await matcher.finish(
                ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("私聊获取黑名单列表必须指定群号！"))
        # 3个参数时将群号放到第一个位置
        params.insert(0, str(ProtocolAdapter.get_msg_type_id(event)))
    if not params[0].isdecimal():
        return await matcher.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("群号错误！"))
    matcher.set_arg("group_id", AdapterMessage(params[0]))


get_black_list = on_command("黑名单列表",
                            rule=to_me(),
                            priority=5,
                            block=True)
get_black_list.__doc__ = """黑名单列表"""
get_black_list.__help_type__ = None
get_black_list.handle()(white_list_handle("group"))
get_black_list.handle()(only_me)
get_black_list.handle()(anslysis_param)


@get_black_list.handle()
async def _(event: AdapterMessageEvent,
            group_id: str = ArgPlainText("group_id")):
    group_id = int(group_id)
    black_list = DBPluginsGroupData.get_user_black_list("group", group_id)
    ret_msg = ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("黑名单列表：\n\n")
    for user_id in black_list:
        ret_msg += ProtocolAdapter.MS.text(str(user_id) + "\n")
    return await get_black_list.finish(ret_msg)
