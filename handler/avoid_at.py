import datetime
from protocol_adapter.adapter_type import AdapterGroupMessageEvent, AdapterBot
from protocol_adapter.protocol_adapter import ProtocolAdapter
from nonebot import on_message
from nonebot.log import logger
from utils import get_time_zone
from utils.permission import white_list_handle
from ..database.group_data import DBPluginsGroupData


def is_avoid_at(
        bot: AdapterBot,
        event: AdapterGroupMessageEvent):
    msg_type = ProtocolAdapter.get_msg_type(event)
    msg_type_id = ProtocolAdapter.get_msg_type_id(event)
    at_lists = ProtocolAdapter.get_at(bot, event)
    for at_user_id in at_lists:
        # 这里无视at全体
        if DBPluginsGroupData.is_user_avoid_at(msg_type, msg_type_id, at_user_id):
            return True
    return False


avoid_at = on_message(priority=5, rule=is_avoid_at, block=False)  # 调低相应级别
avoid_at.handle(white_list_handle("group"))

g_reset_interval = 300      # 重置at次数时间
at_count_dict = {}          # 已经at了多少次


@avoid_at.handle()
async def _(
        bot: AdapterBot,
        event: AdapterGroupMessageEvent):
    msg_type = ProtocolAdapter.get_msg_type(event)
    msg_type_id = ProtocolAdapter.get_msg_type_id(event)
    at_lists = ProtocolAdapter.get_at(bot, event)
    src_user_id = ProtocolAdapter.get_user_id(event)

    if at_count_dict.get(src_user_id) is None:
        at_count_dict[src_user_id] = {}
    if at_count_dict[src_user_id].get(msg_type_id) is None:
        at_count_dict[src_user_id][msg_type_id] = {}

    final_ban_time = 0
    ret_str = ""
    for at_user_id in at_lists:
        if DBPluginsGroupData.is_user_avoid_at(msg_type, msg_type_id, at_user_id):
            # 这个人不允许at
            if at_count_dict[src_user_id][msg_type_id].get(at_user_id) is None:
                at_count_dict[src_user_id][msg_type_id][at_user_id] = {
                    "last_at_time": 0,
                    "at_count": 0,
                }
            last_at_time = at_count_dict[src_user_id][msg_type_id][at_user_id]["last_at_time"]
            at_count = at_count_dict[src_user_id][msg_type_id][at_user_id]["at_count"]

            datetime_now = int(datetime.datetime.now(get_time_zone()).timestamp())
            if datetime_now - last_at_time > g_reset_interval:
                at_count = 0
            at_count += 1
            logger.info(f"src_user_id = {src_user_id} at_user_id = {at_user_id} at_count = {at_count}")
            at_count_dict[src_user_id][msg_type_id][at_user_id]["last_at_time"] = datetime_now
            at_count_dict[src_user_id][msg_type_id][at_user_id]["at_count"] = at_count

            ban_time = DBPluginsGroupData.get_at_punishment_ban_time(msg_type, msg_type_id, at_user_id, at_count)
            # 取最严重的
            if ban_time == -1:
                # 踢出群
                final_ban_time = -1
            elif final_ban_time != -1:
                final_ban_time = max(ban_time, final_ban_time)
            ret_str += DBPluginsGroupData.get_user_at_punishment_ban_text(msg_type, msg_type_id, at_user_id) + "\n"

    # 撤回刚刚那条消息
    await ProtocolAdapter.delete_msg(ProtocolAdapter.get_bot_id(bot), event)
    await ProtocolAdapter.send_message(
        ProtocolAdapter.get_bot_id(bot),
        msg_type,
        msg_type_id,
        ProtocolAdapter.MS.at(src_user_id) + ProtocolAdapter.MS.text(ret_str))
    if final_ban_time == -1:
        # 踢出群
        await ProtocolAdapter.set_group_kick(ProtocolAdapter.get_bot_id(bot), msg_type_id, src_user_id)
    elif final_ban_time != 0:
        # 禁言
        await ProtocolAdapter.set_group_ban(ProtocolAdapter.get_bot_id(bot), msg_type_id, src_user_id, final_ban_time)
