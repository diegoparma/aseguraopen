"""
Agent Orchestrator

Provee una capa ligera para registrar agentes, descubrir sus "tools"/"functions"
y ejecutar/encaminar llamadas entre ellos (handoff).

Este es un orquestador mínimo pensado para integrarse con los agentes
ya existentes en `src/agents` (IntakeAgent, QuotationAgent, ExplorationAgent).
"""
from typing import Any, Callable, Dict, Iterable, Optional
import inspect


class AgentOrchestrator:
    def __init__(self) -> None:
        self.agents: Dict[str, Any] = {}

    def register(self, agent_creator: Any) -> str:
        """Registra un agente a partir de su clase/creator que expone `create_agent()`.

        Devuelve el nombre con el que quedó registrado.
        """
        agent = agent_creator.create_agent()
        name = getattr(agent, "name", None) or getattr(agent_creator, "__name__", "UnknownAgent")
        self.agents[name] = agent
        return name

    def list_agents(self) -> Iterable[str]:
        return list(self.agents.keys())

    def _iter_tools(self, agent: Any):
        for attr in ("tools", "functions"):
            tools = getattr(agent, attr, None)
            if tools:
                for t in tools:
                    yield t

    def find_tool(self, agent_name: str, tool_name: str) -> Optional[Callable]:
        agent = self.agents.get(agent_name)
        if not agent:
            return None
        for t in self._iter_tools(agent):
            t_name = getattr(t, "__name__", None) or getattr(t, "name", None)
            if t_name == tool_name or getattr(t, "tool_name", None) == tool_name:
                return t
        return None

    async def run_tool(self, agent_name: str, tool_name: str, *args, **kwargs):
        """Ejecuta una herramienta/función del agente.

        Devuelve el resultado (awaita si la herramienta es coroutine).
        """
        tool = self.find_tool(agent_name, tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in agent '{agent_name}'")

        result = tool(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    async def handoff(self, from_agent: str, to_agent: str, tool_name: str, *args, **kwargs):
        """Realiza un handoff simple: invoca `tool_name` del `to_agent`.

        `from_agent` sólo se incluye por traza/contexto y para futuras extensiones.
        """
        return await self.run_tool(to_agent, tool_name, *args, **kwargs)


__all__ = ["AgentOrchestrator"]
