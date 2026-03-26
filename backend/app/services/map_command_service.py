"""
Gods-Eye OS — Map Command Service
Manages AI-generated map visualization commands for dynamic highlighting
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
import uuid
import json


CommandType = Literal[
    "highlight",      # Highlight specific countries/regions
    "route",          # Draw trade routes or corridors
    "heatmap",        # Risk/signal density heatmap
    "focus",          # Auto-pan/zoom to region
    "marker",         # Place custom markers
    "overlay",        # Custom data overlay
    "clear",          # Clear specific or all commands
]

CommandPriority = Literal["low", "medium", "high", "critical"]


@dataclass
class MapCommand:
    """A single map visualization command"""
    id: str
    command_type: CommandType
    priority: CommandPriority
    data: Dict[str, Any]
    description: str
    source: str  # Which agent/service generated this
    created_at: str
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "command_type": self.command_type,
            "priority": self.priority,
            "data": self.data,
            "description": self.description,
            "source": self.source,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
        }


class MapCommandService:
    """Manages map visualization commands"""

    def __init__(self):
        self._commands: Dict[str, MapCommand] = {}
        self._command_history: List[MapCommand] = []
        self._max_history = 100

    # ─────────────────────────────────────────────────────────────────────────
    # Command Creation
    # ─────────────────────────────────────────────────────────────────────────

    def create_highlight_command(
        self,
        country_ids: List[str],
        color: str = "#3b82f6",
        pulse: bool = True,
        description: str = "Highlight countries",
        source: str = "system",
        priority: CommandPriority = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MapCommand:
        """Create a command to highlight specific countries"""
        command = MapCommand(
            id=f"cmd-{uuid.uuid4().hex[:8]}",
            command_type="highlight",
            priority=priority,
            data={
                "country_ids": country_ids,
                "color": color,
                "pulse": pulse,
                "radius": 400000,
            },
            description=description,
            source=source,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        self._commands[command.id] = command
        self._add_to_history(command)
        return command

    def create_route_command(
        self,
        from_country: str,
        to_country: str,
        route_type: str = "trade",
        color: str = "#10b981",
        weight: int = 3,
        description: str = "Draw route",
        source: str = "system",
        priority: CommandPriority = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MapCommand:
        """Create a command to draw a route between countries"""
        command = MapCommand(
            id=f"cmd-{uuid.uuid4().hex[:8]}",
            command_type="route",
            priority=priority,
            data={
                "from_country": from_country,
                "to_country": to_country,
                "route_type": route_type,
                "color": color,
                "weight": weight,
                "animated": True,
            },
            description=description,
            source=source,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        self._commands[command.id] = command
        self._add_to_history(command)
        return command

    def create_heatmap_command(
        self,
        data_points: List[Dict[str, Any]],
        metric: str,
        color_scale: str = "red",
        description: str = "Display heatmap",
        source: str = "system",
        priority: CommandPriority = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MapCommand:
        """Create a command to display a heatmap"""
        command = MapCommand(
            id=f"cmd-{uuid.uuid4().hex[:8]}",
            command_type="heatmap",
            priority=priority,
            data={
                "data_points": data_points,
                "metric": metric,
                "color_scale": color_scale,
                "opacity": 0.7,
            },
            description=description,
            source=source,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        self._commands[command.id] = command
        self._add_to_history(command)
        return command

    def create_focus_command(
        self,
        country_id: str,
        zoom_level: int = 5,
        duration_ms: int = 1000,
        description: str = "Focus on region",
        source: str = "system",
        priority: CommandPriority = "high",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MapCommand:
        """Create a command to focus/pan to a specific country"""
        command = MapCommand(
            id=f"cmd-{uuid.uuid4().hex[:8]}",
            command_type="focus",
            priority=priority,
            data={
                "country_id": country_id,
                "zoom_level": zoom_level,
                "duration_ms": duration_ms,
                "smooth": True,
            },
            description=description,
            source=source,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        self._commands[command.id] = command
        self._add_to_history(command)
        return command

    def create_marker_command(
        self,
        lat: float,
        lng: float,
        marker_type: str,
        label: str,
        color: str = "#f59e0b",
        description: str = "Place marker",
        source: str = "system",
        priority: CommandPriority = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MapCommand:
        """Create a command to place a custom marker"""
        command = MapCommand(
            id=f"cmd-{uuid.uuid4().hex[:8]}",
            command_type="marker",
            priority=priority,
            data={
                "lat": lat,
                "lng": lng,
                "marker_type": marker_type,
                "label": label,
                "color": color,
                "icon": "info",
            },
            description=description,
            source=source,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        self._commands[command.id] = command
        self._add_to_history(command)
        return command

    def create_overlay_command(
        self,
        overlay_type: str,
        overlay_data: Dict[str, Any],
        description: str = "Display overlay",
        source: str = "system",
        priority: CommandPriority = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MapCommand:
        """Create a command for custom data overlay"""
        command = MapCommand(
            id=f"cmd-{uuid.uuid4().hex[:8]}",
            command_type="overlay",
            priority=priority,
            data={
                "overlay_type": overlay_type,
                "overlay_data": overlay_data,
            },
            description=description,
            source=source,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        self._commands[command.id] = command
        self._add_to_history(command)
        return command

    # ─────────────────────────────────────────────────────────────────────────
    # Command Management
    # ─────────────────────────────────────────────────────────────────────────

    def get_all_commands(self) -> List[Dict[str, Any]]:
        """Get all active map commands sorted by priority"""
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        commands = sorted(
            self._commands.values(),
            key=lambda c: priority_order.get(c.priority, 0),
            reverse=True,
        )
        return [cmd.to_dict() for cmd in commands]

    def get_command(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific command by ID"""
        command = self._commands.get(command_id)
        return command.to_dict() if command else None

    def get_commands_by_type(self, command_type: CommandType) -> List[Dict[str, Any]]:
        """Get all commands of a specific type"""
        commands = [
            cmd.to_dict()
            for cmd in self._commands.values()
            if cmd.command_type == command_type
        ]
        return commands

    def get_commands_by_source(self, source: str) -> List[Dict[str, Any]]:
        """Get all commands from a specific source"""
        commands = [
            cmd.to_dict()
            for cmd in self._commands.values()
            if cmd.source == source
        ]
        return commands

    def remove_command(self, command_id: str) -> bool:
        """Remove a specific command"""
        if command_id in self._commands:
            del self._commands[command_id]
            return True
        return False

    def clear_commands(
        self,
        command_type: Optional[CommandType] = None,
        source: Optional[str] = None,
    ) -> int:
        """Clear commands by type or source, or all if neither specified"""
        removed = 0

        if command_type is None and source is None:
            # Clear all
            removed = len(self._commands)
            self._commands.clear()
        else:
            # Clear by filter
            to_remove = []
            for cmd_id, cmd in self._commands.items():
                if (command_type is None or cmd.command_type == command_type) and \
                   (source is None or cmd.source == source):
                    to_remove.append(cmd_id)

            for cmd_id in to_remove:
                del self._commands[cmd_id]
                removed += 1

        return removed

    def get_command_summary(self) -> Dict[str, Any]:
        """Get a summary of current map state"""
        by_type = {}
        by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_source = {}

        for cmd in self._commands.values():
            # Count by type
            by_type[cmd.command_type] = by_type.get(cmd.command_type, 0) + 1

            # Count by priority
            by_priority[cmd.priority] += 1

            # Count by source
            by_source[cmd.source] = by_source.get(cmd.source, 0) + 1

        return {
            "total_commands": len(self._commands),
            "by_type": by_type,
            "by_priority": by_priority,
            "by_source": by_source,
            "history_size": len(self._command_history),
        }

    def _add_to_history(self, command: MapCommand):
        """Add command to history, maintaining max size"""
        self._command_history.append(command)
        if len(self._command_history) > self._max_history:
            self._command_history.pop(0)

    def get_command_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent command history"""
        history = self._command_history[-limit:]
        return [cmd.to_dict() for cmd in reversed(history)]


# Global singleton instance
_map_command_service = MapCommandService()


def get_map_command_service() -> MapCommandService:
    """Get the global map command service instance"""
    return _map_command_service
