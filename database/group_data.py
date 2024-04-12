import copy
import re
from typing import List
from database.interface.db_impl_interface import DBNoCacheImplInterface
from database.db_manager import DBManager


# 群组
class DBPluginsGroupData(DBNoCacheImplInterface):
    """
    key: {msg_type}_{msg_type_id}_{user_id}
    """
    _default_value = {
        # 时间是以逗号分割的
        # 例如：30,1800,86400,-1 ，即第一次30分钟，第二次1800分钟，第三次86400分钟，第四次踢出群
        # 0表示不禁言，-1表示直接踢出群
        "at_punishment_ban_rule": "0",
        "at_punishment_ban_text": "",
        "is_black": False,
    }

    @classmethod
    def set_user_avoid_at(cls, msg_type: str, msg_type_id: int, user_id: int):
        """ 设置用户禁止被at """
        key = cls.generate_key(msg_type, msg_type_id, user_id)
        data = cls.get_data_by_key(key)
        if data is None:
            data = copy.deepcopy(cls._default_value)
        cls.set_data_by_key(key, data)

    @classmethod
    def is_user_avoid_at(cls, msg_type: str, msg_type_id: int, user_id: int) -> bool:
        """ 是否该用户禁止被at """
        key = cls.generate_key(msg_type, msg_type_id, user_id)
        data = cls.get_data_by_key(key)
        return data is not None

    @classmethod
    def set_user_at_punishment_ban_rule(cls, msg_type: str, msg_type_id: int, user_id: int, ban_rule: str):
        """ 设置被at后惩罚规则 """
        key = cls.generate_key(msg_type, msg_type_id, user_id)
        data = cls.get_data_by_key(key)
        if data is None:
            data = copy.deepcopy(cls._default_value)
        data["at_punishment_ban_rule"] = ban_rule
        cls.set_data_by_key(key, data)

    @classmethod
    def get_at_punishment_ban_time(cls, msg_type: str, msg_type_id: int, user_id: int, at_count: int) -> int:
        """ 根据当前at次数 获取封禁时间  """
        key = cls.generate_key(msg_type, msg_type_id, user_id)
        data = cls.get_data_by_key(key)
        if data is None:
            return 0
        else:
            ban_group = data["at_punishment_ban_rule"].split(",")
            if len(ban_group) == 0:
                return 0
            elif len(ban_group) <= at_count:
                return int(ban_group[-1])
            else:
                return int(ban_group[at_count - 1])

    @classmethod
    def set_user_at_punishment_ban_text(cls, msg_type: str, msg_type_id: int, user_id: int, ban_text: str):
        """ 设置被at后惩罚内容 """
        key = cls.generate_key(msg_type, msg_type_id, user_id)
        data = cls.get_data_by_key(key)
        if data is None:
            data = copy.deepcopy(cls._default_value)
        data["at_punishment_ban_text"] = ban_text
        cls.set_data_by_key(key, data)

    @classmethod
    def get_user_at_punishment_ban_text(cls, msg_type: str, msg_type_id: int, user_id: int) -> str:
        """ 获取被at后惩罚内容 """
        key = cls.generate_key(msg_type, msg_type_id, user_id)
        data = cls.get_data_by_key(key)
        if data is None:
            return ""
        return data["at_punishment_ban_text"]

    @classmethod
    def is_user_in_black_list(cls, msg_type: str, msg_type_id: int, user_id: int) -> bool:
        """ 判断用户是否在群组黑名单中 """
        key = cls.generate_key(msg_type, msg_type_id, user_id)
        data = cls.get_data_by_key(key)
        if data is None:
            return False
        return data["is_black"]

    @classmethod
    def add_user_to_black_list(cls, msg_type: str, msg_type_id: int, user_id: int):
        """ 将用户新增至群组黑名单中 """
        key = cls.generate_key(msg_type, msg_type_id, user_id)
        data = cls.get_data_by_key(key)
        if data is None:
            data = copy.deepcopy(cls._default_value)
        data["is_black"] = True
        cls.set_data_by_key(key, data)

    @classmethod
    def remove_user_from_black_list(cls, msg_type: str, msg_type_id: int, user_id: int):
        """ 将用户从群组黑名单中移除 """
        key = cls.generate_key(msg_type, msg_type_id, user_id)
        data = cls.get_data_by_key(key)
        if data is None:
            return
        data["is_black"] = False
        cls.set_data_by_key(key, data)

    @classmethod
    def get_user_black_list(cls, msg_type: str, msg_type_id: int) -> List[int]:
        """ 获取当前群组黑名单列表 """
        black_list = []
        for key, item in cls.get_data().items():
            key_info = cls.analysis_key(key)
            if msg_type == key_info["msg_type"] and msg_type_id == key_info["msg_type_id"] and item.get("is_black"):
                black_list.append(key_info["user_id"])
        return black_list

    @classmethod
    def db_key_name(cls, bot_id):
        # 公共的
        return f"{cls.__name__}_BOT_{bot_id}"

    @classmethod
    async def init(cls):
        """ 初始化 """
        pass

    @classmethod
    def generate_key(cls, msg_type, msg_type_id, user_id):
        """ 生成__data内存放的key """
        return f"{msg_type}_{msg_type_id}_{user_id}"

    @classmethod
    def analysis_key(cls, key):
        """ 解析generate_key生成的key """
        regex_groups = re.match("([a-zA-Z]*)_([0-9]*)_([0-9]*)", key).groups()
        if regex_groups is not None:
            return {
                "msg_type": regex_groups[0],
                "msg_type_id": int(regex_groups[1]),
                "user_id": int(regex_groups[2])
            }


DBManager.add_db(DBPluginsGroupData)
