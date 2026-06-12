from app.im.base import IMAdapter
from app.im.feishu.adapter import FeishuAdapter
from app.im.web.adapter import WebAdapter


class IMAdapterRegistry:
    _adapters: dict[str, IMAdapter] = {}

    @classmethod
    def get_adapter(cls, channel: str) -> IMAdapter | None:
        if channel not in cls._adapters:
            adapter = cls._create_adapter(channel)
            if adapter:
                cls._adapters[channel] = adapter
        return cls._adapters.get(channel)

    @classmethod
    def _create_adapter(cls, channel: str) -> IMAdapter | None:
        if channel == "feishu":
            return FeishuAdapter()
        elif channel == "web":
            return WebAdapter()
        return None

    @classmethod
    def register_adapter(cls, channel: str, adapter: IMAdapter) -> None:
        cls._adapters[channel] = adapter
