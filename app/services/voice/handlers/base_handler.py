from abc import ABC, abstractmethod


class BaseVoiceHandler(ABC):

    name: str

    @property
    @abstractmethod
    def system_instruction(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def tools(self) -> list:
        raise NotImplementedError

    @property
    def ends_session_after_tool_call(self) -> bool:
        return False

    @abstractmethod
    async def handle_tool_call(
        self,
        call: dict,
        sio,
        sid: str,
    ):
        raise NotImplementedError