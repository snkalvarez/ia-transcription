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

    def should_end_session_after_tool_call(self, tool_name: str) -> bool:
        return self.ends_session_after_tool_call

    @abstractmethod
    async def handle_tool_call(
        self,
        call: dict,
        sio,
        sid: str,
        numero_ingreso: str | None = None,
    ):
        raise NotImplementedError