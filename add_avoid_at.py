import copy

from nonebot import on_command
from nonebot.internal.matcher import Matcher
from protocol_adapter.protocol_adapter import ProtocolAdapter
from protocol_adapter.adapter_type import AdapterMessage, AdapterBot, AdapterMessageEvent, AdapterGroupMessageEvent
from nonebot.rule import to_me
from nonebot.params import ArgPlainText, CommandArg
from .database.group_data import DBPluginsGroupData
from utils.permission import white_list_handle, only_me


async def get_user_id(
    bot: AdapterBot,
    matcher: Matcher,
    event: AdapterMessageEvent,
    command_arg: AdapterMessage = CommandArg(),
):
    data = command_arg.extract_plain_text().split(" ")
    # 参数：（群号可选） userID 规则（例：0,30,1800,86400,-1） 提示语
    if len(data) != 3 and len(data) != 4:
        return await matcher.finish(
            ProtocolAdapter.MS.reply(event) +
            ProtocolAdapter.MS.text("参数错误！参数列表：1.群号（可选） 2.userID 3.规则（例：0,30,1800,86400,-1） 4.提示语"))
    params = copy.deepcopy(data)
    if len(params) == 3:
        if not isinstance(event, AdapterGroupMessageEvent):
            return await matcher.finish(
                ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("私聊添加禁止at必须指定群号！"))
        # 3个参数时将群号放到第一个位置
        params.insert(0, str(ProtocolAdapter.get_msg_type_id(event)))
    if not params[0].isdecimal():
        return await matcher.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("群号错误！"))
    if not params[1].isdecimal():
        return await matcher.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("目标用户ID错误！"))
    if len(params[2].replace(" ", "").split(",")) == 0:
        return await matcher.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("规则错误！长度为0！"))
    ban_rule_str = ""
    for ban_time in params[2].replace(" ", "").split(","):
        try:
            int(ban_time)
        except ValueError:
            # 如果规则长度为0 或者规则中有非数字存在
            return await matcher.finish(
                ProtocolAdapter.MS.reply(event) +
                ProtocolAdapter.MS.text("规则错误！请检查规则是否为以逗号分割的纯数字！"))
        ban_rule_str += ban_time + ","
    ban_rule_str = ban_rule_str[:len(ban_rule_str) - 1]
    matcher.set_arg("group_id", AdapterMessage(params[0]))
    matcher.set_arg("user_id", AdapterMessage(params[1]))
    matcher.set_arg("ban_rule", AdapterMessage(ban_rule_str))
    matcher.set_arg("ban_text", AdapterMessage(params[3]))


add_avoid_at = on_command("添加禁止at",
                          rule=to_me(),
                          priority=5,
                          block=True)
add_avoid_at.__doc__ = """添加禁止at"""
add_avoid_at.__help_type__ = None
add_avoid_at.handle()(white_list_handle("group"))
add_avoid_at.handle()(only_me)
add_avoid_at.handle()(get_user_id)


@add_avoid_at.handle()
async def _(event: AdapterMessageEvent,
            group_id: str = ArgPlainText("group_id"),
            user_id: str = ArgPlainText("user_id"),
            ban_rule: str = ArgPlainText("ban_rule"),
            ban_text: str = ArgPlainText("ban_text")):
    group_id = int(group_id)
    user_id = int(user_id)
    if DBPluginsGroupData.is_user_avoid_at("group", group_id, user_id):
        return add_avoid_at.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("已存在该用户的禁止at规则"))
    DBPluginsGroupData.set_user_avoid_at("group", group_id, user_id)
    DBPluginsGroupData.set_user_at_punishment_ban_rule("group", group_id, user_id, ban_rule)
    DBPluginsGroupData.set_user_at_punishment_ban_text("group", group_id, user_id, ban_text)

    ret_str = f"已添加用户{user_id}的禁止at规则：\n"
    ban_rule_list = ban_rule.split(",")
    for i in range(len(ban_rule_list)):
        ban_time = ban_rule_list[i]
        if ban_time == "0":
            ban_time_str = "不封禁"
        elif ban_time == "-1":
            ban_time_str = "移出群聊"
        else:
            ban_time_str = f"封禁{ban_time}秒"
        ret_str += f"第{i + 1}次：{ban_time_str}\n"
    return await add_avoid_at.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text(ret_str))
