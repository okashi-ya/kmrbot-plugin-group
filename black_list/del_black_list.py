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
    # 参数：（群号可选） userID
    if len(data) != 1 and len(data) != 2:
        return await matcher.finish(
            ProtocolAdapter.MS.reply(event) +
            ProtocolAdapter.MS.text("参数错误！参数列表：1.群号（可选） 2.userID"))
    params = copy.deepcopy(data)
    if len(params) == 1:
        if not isinstance(event, AdapterGroupMessageEvent):
            return await matcher.finish(
                ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("私聊移除黑名单必须指定群号！"))
        # 3个参数时将群号放到第一个位置
        params.insert(0, str(ProtocolAdapter.get_msg_type_id(event)))
    if not params[0].isdecimal():
        return await matcher.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("群号错误！"))
    if not params[1].isdecimal():
        return await matcher.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("目标用户ID错误！"))
    matcher.set_arg("group_id", AdapterMessage(params[0]))
    matcher.set_arg("user_id", AdapterMessage(params[1]))


del_black_list = on_command("移除黑名单",
                            rule=to_me(),
                            priority=5,
                            block=True)
del_black_list.__doc__ = """移除黑名单"""
del_black_list.__help_type__ = None
del_black_list.handle()(white_list_handle("group"))
del_black_list.handle()(only_me)
del_black_list.handle()(anslysis_param)


@del_black_list.handle()
async def _(event: AdapterMessageEvent,
            group_id: str = ArgPlainText("group_id"),
            user_id: str = ArgPlainText("user_id")):
    group_id = int(group_id)
    user_id = int(user_id)
    if not DBPluginsGroupData.is_user_in_black_list("group", group_id, user_id):
        return del_black_list.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("黑名单中不存在该用户。"))
    DBPluginsGroupData.remove_user_from_black_list("group", group_id, user_id)
    return await del_black_list.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("已从黑名单中移除。"))
